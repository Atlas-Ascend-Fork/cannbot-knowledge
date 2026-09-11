---
type: Concept
title: GDN Chunk 算子（solve_tril / chunk_delta_h / chunk_o / wy_fast Triton 核）
description: 门控 DeltaNet（GDN）线性注意力 prefill/训练侧的 chunk-parallel Triton 算子族（MindSpeed core mindspeed/ops/triton，经 triton-on-ascend 后端落昇腾），由 MindSpeed-LLM 的 ChunkGatedDeltaRuleFunction 串成正反向。算子链：chunk_local_cumsum（log 门控 g 前缀和）→ chunk_scaled_dot_kkt（β·tril(KKᵀ)·门控衰减）→ solve_tril（严格下三角求 (I+A)⁻¹，前代求逆 + 16×16→32×32 Schur 补块合并，WY/UT 变换核心）→ recompute_w_u_fwd（WY 表示 u=A@βv、w=A@β·e^g·k）→ chunk_gated_delta_rule_fwd_h（隐状态 h∈R^{K×V} 的 chunk 间门控扫描：v_res=u−w@h、g/gk 门控、h+=k@v_res、K 沿 64 拆块、h0/ht、cu_seqlens 变长）→ chunk_fwd_o（O=scale·Q@h+scale·tril(QKᵀ⊙门控)@v_new，grid=24 少核持久化）。反向 dv_local/dhu/dqkwg/wy_repr_bwd 与正向对偶。仅 bf16、fp32 累加；与推理 decode 侧 recurrent_gated_delta_rule 同属一条 delta-rule 的两种时间分解。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/solve_tril.py
  role: supporting
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# GDN Chunk 算子（solve_tril / chunk_delta_h / chunk_o / wy_fast Triton 核）

## Summary

门控 DeltaNet（GDN）线性注意力在 prefill / 训练阶段走 **chunk-parallel** 形式：把序列切成长 `BT=64` 的 chunk，chunk 内用 WY/UT 表示把 delta-rule 的逐 token 状态递推转成矩阵运算并行算，chunk 间再串行扫描隐状态 $h\in\mathbb{R}^{K\times V}$。这套分解由 MindSpeed core `mindspeed/ops/triton/` 下一族 Triton 核承载，经 [triton-on-ascend](../frameworks/triton_on_ascend.md) 后端降级到昇腾 Cube/Vector；上层由 MindSpeed-LLM 的 `ChunkGatedDeltaRuleFunction`（`torch.autograd.Function`）按固定顺序把这些核串成正反向。

输入 q/k 形状 `[B,T,H,K]`、v 形状 `[B,T,H,V]`，log 空间 forget gate `g` 与写入强度 `beta` 形状 `[B,T,H]`，chunk 长 `BT=64`，`K≤256`（沿 64 维拆至多 4 子块），隐状态 `[N,H,K,V]`。仅支持 bf16（传 fp32 抛错）、fp32 累加；变长序列经 `cu_seqlens`（batch=1，FlashAttention 风格），训练不支持传入 `initial_state`。`scale` 默认 `1/√K`。

它与推理 decode 侧的逐 token 融合算子 [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md) 是同一 delta-rule 状态更新的两种时间分解：recurrent 形式按单 token 顺序推进 state，chunk 形式块内并行、块间扫描。

## 正向算子链与各核位置

`ChunkGatedDeltaRuleFunction.forward`（`use_qk_l2norm_in_kernel` 时先对 q/k 做 `l2norm_fwd`）按如下顺序下发，前一核的输出喂下一核：

```
chunk_local_cumsum(g)          # g 的 chunk 内前缀和（log 门控累积）
  → chunk_scaled_dot_kkt_fwd   # A = β·tril(K Kᵀ)·exp(g_i−g_j)，chunk 内严格下三角
  → solve_tril(A)              # A ← (I+A)⁻¹，chunk 内下三角求逆（WY/UT 变换核心）
  → recompute_w_u_fwd          # u = A@(β·v)、w = A@(β·e^g·k)，构造 WY 表示
  → chunk_gated_delta_rule_fwd_h   # 隐状态 h 的 chunk 间门控扫描，出 h / v_new
  → chunk_fwd_o                # O = scale·(Q@h) + scale·tril(Q Kᵀ·e^{g_i−g_j})@v_new
```

### solve_tril — chunk 内 (I+A)⁻¹

对严格下三角矩阵 $A$（`A.triu()==0`）求 $(I+A)^{-1}$，`BT∈{16,32,64}`。`solve_tril_64x64_kernel` / `solve_tril_16x16_kernel` 走按行前代（forward substitution）：取 `b_A = -A`（严格下三角），逐行 `i` 从 2 起算 `b_a = -A[i] + Σ_row(b_a ⊙ b_A)`、写回第 `i` 行，末了 `b_A += I`，得到的就是 delta-rule「$I$ 减严格下三角」那一项的逆。`BT=32` 不直接前代，而是 `merge_16x16_to_32x32_inverse_kernel` 先分别求两个对角 16×16 块的逆 $A^{-1}_{11},A^{-1}_{22}$，再用 Schur 补合成下三角块 $A^{-1}_{21}=-A^{-1}_{22}\,A_{21}\,A^{-1}_{11}$。`DOT_PRECISION` 由 `FLA_TRIL_PRECISION`（默认 `ieee`）控制，NPU 上 `USE_TMA=False` 一律走 `tl.make_block_ptr`。这一步把 chunk 内 delta-rule 的串行依赖转成一次可并行的矩阵求逆，是 WY/UT 表示能成立的关键。

### chunk_scaled_dot_kkt — chunk 内 β·K·Kᵀ 与门控衰减

`chunk_scaled_dot_kkt_fwd` 算待求逆矩阵 $A$ 的非对角部分，输出 `[B,T,H,BT]`。`chunk_scaled_dot_kkt_fwd_kernel`（标量门控 `g` 路径）逐 chunk：`dot = K@Kᵀ`，按严格下三角（`row>col`）与序列有效位 mask，若 `USE_G` 再乘 `exp(g_i − g_j)`（钳到 ±50），最后逐行乘 `β`。即

$$A_{ij} = \beta_i\,(k_i\!\cdot\!k_j)\,e^{\,g_i-g_j}\,[\,i>j\,].$$

带逐通道键门 `gk` 时改走 `..._intra_sub_inter` + `..._intra_sub_intra` 两个子核，把 `gk` 的 chunk 内累积按 `exp(g − gn)`（`gn` 为子块起点门控）补偿到 K 上再点积。这是 solve_tril 的输入。

### wy_fast — WY 表示的 w / u 向量

`recompute_w_u_fwd` 用 solve_tril 出的 $A=(I+\cdot)^{-1}$ 构造 WY 表示两组向量：值侧 `u = A@(β·v)`（`b_vb = v·β`，`b_u = dot(A, b_vb)`，即被 delta 修正后的「新值」），键侧 `w = A@(β·e^g·k)`（`b_kb = k·β·exp(g)`，带 `gk` 时再 `·exp(gk)`，`b_w = dot(A, b_kb)`）。`u`/`w` 随后分别作为 `chunk_gated_delta_rule_fwd_h` 的 `v`/`w` 输入。反向 `prepare_wy_repr_bwd` 由 `dw/du` 反传 `dk/dv/dbeta/dg`，其中对 $A$ 自身的反传是二次夹积 `b_dA = −A·masked·A`（masked 为掩码后的累积梯度）再经 `exp(g_i−g_j)` 门控。

### chunk_delta_h — chunk 间隐状态门控扫描

`chunk_gated_delta_rule_fwd_kernel_h_blockdim64` 是隐状态 $h\in\mathbb{R}^{K\times V}$ 的本体扫描，`K` 沿 64 维拆至多 4 子块（`b_h1..b_h4`，故 `K≤256`），`V` 取 `BV=128`。正序遍历 chunk `i_t`：

- 先把当前 `h_t` 写出到 `h[i_t]`（供 chunk_o 与反向复用）；
- 算残差 `v_res = u − w@h`（`b_v = u_chunk − Σ_block w_block@h_block`），`SAVE_NEW_VALUE` 时把 `v_res` 写出为 `v_new`；
- 输出门 `g`：`v_res *= mask·exp(g_last − g)`，同时 `h *= exp(g_last)`；
- 键门 `gk`：`h *= exp(gk_last)`，并对 K 做 `k *= exp(gk_last − gk)`；
- 状态累加 `h += k@v_res`（`b_h += dot(b_k, b_v)`）。

`g_last`/`gk_last` 取 chunk 末位、且 `g`/`gk` 已是 chunk_local_cumsum 后的累积量。`USE_INITIAL_STATE` 时起始载入 `h0`，`STORE_FINAL_STATE` 时末尾写出 `ht`；`IS_VARLEN` 经 `cu_seqlens`/`chunk_offsets` 定位每条序列的 chunk 区间与隐状态偏移。

### chunk_o — chunk 内注意力 + 跨 chunk Q@h 合成输出

`chunk_fwd_o`（`chunk_fwd_kernel_o`）算最终输出 `O`。逐 chunk：跨 chunk 项 `b_o = Σ_k Q_chunk@h_block`（`Q@h`），chunk 内分数 `b_A = Q@Kᵀ`；若 `USE_G` 则 `b_o *= exp(g)`、`b_A *= exp(g_i − g_j)`；`b_A` 再按因果下三角（`o_i ≥ o_j`）mask；最后

$$O = \text{scale}\cdot(Q@h) + \text{scale}\cdot\big(\text{tril}(Q K^\top\!\odot e^{\,g_i-g_j})\big)@v_{\text{new}}.$$

即跨 chunk 隐状态贡献 `Q@h` 与 chunk 内因果注意力两项各经 `g` 门控后相加再乘 `scale`。`v_new` 用的是 chunk_delta_h 写出的残差值。此核走 [triton-on-ascend](../frameworks/triton_on_ascend.md) 的少核持久化排布：`grid=(24,)`，核内用 `core_id`/`num_programs` 把 `NT` 个 chunk 手动均分到各核循环处理，而非「一 chunk 一 program」。

### cumsum / l2norm — 门控前缀和与 q/k 归一

`chunk_local_cumsum` 对 log forget gate `g` 做 chunk 内（`CHUNK_SIZE=64`）前缀和，`reverse=True` 用于反向 `dg` 的回卷；它为上面所有 `exp(g_i−g_j)` / `exp(g_last−g)` 门控提供累积量。`l2norm`（`l2norm_fwd`/`l2norm_bwd`）在 `use_qk_l2norm_in_kernel` 时对 q/k 末维做 L2 归一 `y = x/√(Σx²+eps)` 并存 `rstd` 供反向，对应 GDN 里 Q/K 的单位范数约束。

## 反向链路

`chunk_gated_delta_rule_bwd` 先用 `recompute_w_u_fwd` / `chunk_gated_delta_rule_fwd_h` 重算 `w,u,h,v_new`（重计算省激活），再依次：

- `chunk_bwd_dv_local` 出 chunk 内 `dv`：`A=K@Q` 经 `exp(g_j−g_i)` 门控与因果掩码后 `@do`；
- `chunk_gated_delta_rule_bwd_dhu` 逆序扫描出 `dh / dh0 / dv2`：用末态梯度 `dht`，每 chunk `dh = scale·(q·e^g)@do − w@dv`，带 `g`/`gk` 衰减，K 同样沿 64 拆块；
- `chunk_bwd_dqkwg` 用重算的 `h` 与 `dh` 出 `dq / dk / dw / dg`；
- `prepare_wy_repr_bwd` 出 `dk2 / dv / dbeta / dg2`，其中 `dk2`、`dg2` 分别加回上一步的 `dk`、`dg`；
- `dg` 末了再走一次 `chunk_local_cumsum(reverse=True)` 完成门控梯度回卷。

`use_qk_l2norm_in_kernel` 时 `dq/dk` 末尾经 `l2norm_bwd` 回传归一化。整条反向的算子顺序与正向算子链严格对偶。

## 与推理侧 recurrent 形式对照

两侧是同一 delta-rule 状态更新（state 经 `diag(e^g)` 衰减 + `β` 写入 `k⊗v` 的修正、`out = q·state`）的不同时间分解：

- chunk 形式（本族算子）把 chunk 内的逐 token 串行依赖经 `chunk_scaled_dot_kkt` + `solve_tril` + `recompute_w_u_fwd` 转成矩阵求逆与两次矩阵乘并行算，chunk 间才用 `chunk_delta_h` 串行扫隐状态 `h`；适合 prefill / 训练（要算前反向、序列长）。
- recurrent 形式 [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md) 直接逐 token 推进 `ssm_state`，一次 launch 完成 Sigmoid + L2Norm + Gated-Delta 递推 + state 写回；适合 decode / MTP（单步或少量 draft token）。

GDN 模块整体结构语义见跨域 [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)；训练侧 DeltaNet（无门控纯 Delta Rule）入门样例与 Triton 算子性能对照见 [deltanet-pretrain](../../guides/recipes/deltanet_pretrain.md)。

## Evidence

- [mindspeed](https://gitcode.com/ascend/MindSpeed) — MindSpeed core @1432cb0
  - [`mindspeed/ops/triton/solve_tril.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/solve_tril.py)（`solve_tril` / `solve_tril_64x64_kernel` / `solve_tril_16x16_kernel` 前代求逆得 $(I+A)^{-1}$；`merge_16x16_to_32x32_inverse_kernel` 的 Schur 补 $A^{-1}_{21}=-A^{-1}_{22}A_{21}A^{-1}_{11}$；`USE_TMA=False`）
  - [`mindspeed/ops/triton/chunk_scaled_dot_kkt.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/chunk_scaled_dot_kkt.py)（`chunk_scaled_dot_kkt_fwd` / `..._kernel`：`β·tril(KKᵀ)·exp(g_i−g_j)`、±50 钳位；`gk` 走 `intra_sub_inter`+`intra_sub_intra`）
  - [`mindspeed/ops/triton/wy_fast.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/wy_fast.py)（`recompute_w_u_fwd`：`u=A@(βv)`、`w=A@(β·e^g·k)`；`prepare_wy_repr_bwd` 出 `dk/dv/dbeta/dg`）
  - [`mindspeed/ops/triton/chunk_delta_h.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/chunk_delta_h.py)（`chunk_gated_delta_rule_fwd_h` / `chunk_gated_delta_rule_fwd_kernel_h_blockdim64`：`v_res=u−w@h`、`g`/`gk` 门控、`h+=k@v_res`、K 沿 64 拆 4 块、`h0`/`ht`、`cu_seqlens` 变长；反向 `chunk_gated_delta_rule_bwd_dhu` 出 `dh/dh0/dv2`）
  - [`mindspeed/ops/triton/chunk_o.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/chunk_o.py)（`chunk_fwd_o` / `chunk_fwd_kernel_o`：`O=scale·Q@h + scale·tril(QKᵀ⊙e^{g_i−g_j})@v_new`、`grid=(24,)` 少核持久化手动均分；`chunk_bwd_dqkwg` 出 `dq/dk/dw/dg`、`chunk_bwd_dv_local` 出 `dv`）
  - [`mindspeed/ops/triton/cumsum.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/cumsum.py)（`chunk_local_cumsum`：log 门控 `g` 的 chunk 内前缀和、`reverse` 反向回卷）
  - [`mindspeed/ops/triton/l2norm.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/ops/triton/l2norm.py)（`l2norm_fwd`/`l2norm_bwd`：`y=x/√(Σx²+eps)` 存 `rstd`，q/k 单位范数）
  - [`tests_extend/unit_tests/ops/triton/`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/tests_extend/unit_tests/ops/triton)（`test_solve_tril.py` / `test_chunk_scaled_dot_kkt_fwd.py` / `test_prepare_wy_repr_bwd.py` / `test_chunk_gated_delta_rule_fwd_h.py` / `test_chunk_gated_delta_rule_bwd_dhu.py` / `test_chunk_o.py` / `test_chunk_bwd_dqkwg.py` / `test_chunk_bwd_dv_local.py` / `test_cumsum.py` / `test_l2norm_fwd.py` 逐核佐证算子语义）
- [mindspeed](https://gitcode.com/ascend/MindSpeed) — MindSpeed-LLM @183e02c
  - [`mindspeed_llm/tasks/models/transformer/chunk_gated_delta_rule.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/chunk_gated_delta_rule.py)（`ChunkGatedDeltaRuleFunction` / `chunk_gated_delta_rule_fwd` / `chunk_gated_delta_rule_bwd`：正反向算子链编排、bf16-only、`scale=1/√K`、`cu_seqlens` 变长、`use_qk_l2norm_in_kernel`）

## Links

- [triton-on-ascend](../frameworks/triton_on_ascend.md)（承载本算子族的昇腾 Triton 后端：少核持久化 grid、NPU autotune 旋钮、block_ptr→UB DMA 映射）
- [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md)（跨域：同一 delta-rule 的 decode 逐 token recurrent 形式，与本族 chunk 形式互为时间分解）
- [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)（跨域：GDN 线性注意力模块整体结构语义，Prefill ChunkGDN 即本算子族的语义对应）
- [deltanet-pretrain](../../guides/recipes/deltanet_pretrain.md)（同域：训练侧 DeltaNet 线性注意力样例，Triton 算子在 NPU 上的前/反向性能对照）
- [mindspeed](https://gitcode.com/ascend/MindSpeed) — MindSpeed core @1432cb0 / MindSpeed-LLM @183e02c（`ops/triton` GDN chunk 核源与 autograd 封装）
- [gated-deltanet-train](../modules/gated_deltanet_train.md)（调用这组 chunk 算子的 GDN 训练模块：三套后端、autograd 编排、GDN CP）