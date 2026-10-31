---
type: Concept
title: Gated DeltaNet 训练（Chunk 并行 / Flash 递归 / GDN 上下文并行）
description: MindSpeed-LLM 训练侧 Gated DeltaNet（GDN）线性注意力模块，覆盖 Qwen3-Next 与稠密/混合 GatedDeltaNet 预训练。当前 mcore 与 FSDP2 实现的 chunk 反向、三套后端和 GDN 上下文并行边界；旧启动样例已移除。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/models/transformer/qwen3_next_gated_deltanet_attention.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/fsdp2/models/qwen3_next/modeling_qwen3_next.py
  role: implementation
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- agnostic
---

# Gated DeltaNet 训练（Chunk 并行 / Flash 递归 / GDN 上下文并行）

## Summary

MindSpeed-LLM 把 Gated DeltaNet（GDN）线性注意力搬到训练侧：Qwen3-Next 及稠密/混合 GatedDeltaNet 模型在昇腾 NPU 上从头预训练时，GDN 层既要算前向，也要算反向梯度，并要在长序列下沿 chunk 切块并行、在多卡下做上下文并行。GDN 的概念定义（in_proj → Causal Conv1d → 门控 → Delta Rule 递推 → 输出 RMSNorm+Gate）见推理侧 [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)，此处只记训练侧新增的三件事：带完整反向的 **chunk gated delta rule**（torch 参考 / Triton / Flash-AscendC 三套后端）、decode-cache 路径的 **逐步递归**形式、以及 GDN 专属的 **上下文并行**（沿 head 而非沿序列切）。chunk 算子的逐阶段实现细节链 [gdn-chunk-kernels](../kernels/gdn_chunk_kernels.md)。

GDN 在 MindSpeed-LLM 有两条训练入口，结构同源、并行能力不同：

- **mcore spec 路径** `CustomQwen3NextGatedDeltaNetAttention`（`MegatronModule`），由 `qwen3_next_spec` 装配；其 `__init__` 显式 `raise AssertionError`：`tensor_model_parallel_size > 1 or context_parallel_size > 1` 不支持，GDN 层只能复制、靠 DP 扩展。
- **FSDP2 路径** `Qwen3NextGatedDeltaNet`（`mindspeed_llm/fsdp2/models/qwen3_next/`），支持 `--use-flash-gdn` 的 AscendC 融合后端，并通过 `gdn_forward_with_cp` 获得上下文并行能力。

## 训练侧模块结构

两条入口的层结构一致。输入 hidden state 经两个投影：

- `in_proj_qkvz`：输出维 `projection_size_qkvz = key_dim*2 + value_dim*2`，一次产出 Q/K/V 与门控 Z；
- `in_proj_ba`：输出维 `num_v_heads*2`，产出 Delta Rule 的写入强度 `b` 与时间步参数 `a`。

`fix_query_key_value_ordering` 按 `num_k_heads` 把 `mixed_qkvz` 拆成 `query/key/value/z`、把 `mixed_ba` 拆成 `b/a`，其中 V/Z 按 `num_v_heads // num_k_heads` 展开成 GQA 分组。`conv1d` 是分组深度卷积，`conv_dim = key_dim*2 + value_dim`、`groups=conv_dim`、`kernel_size = mamba_d_conv`、`padding = kernel_size-1`，在序列维做因果短卷积后接 SiLU。

门控量由可训练参数推出：

```python
beta = b.sigmoid()
g = -self.A_log.float().exp() * F.softplus(a.float() + self.dt_bias)
```

`A_log`（初始 `log(uniform(0,16))`）与 `dt_bias`（初始全 1）是每 value-head 一个标量的可训练参数，`g` 是 log 空间的 forget gate。`num_v_heads > num_k_heads` 时 `query/key` 沿 head 维 `repeat_interleave` 补齐 GQA。Delta Rule 输出经 `Qwen3NextRMSNormGated`（FP32 RMSNorm 后乘 `SiLU(z)` 门控，`norm before gate`）归一化，再过 `out_proj` 投回 hidden。q/k 的 L2 归一化由 `use_qk_l2norm_in_kernel=True` 在算子内部完成（`l2norm`，eps=1e-6）。

## Chunk Gated Delta Rule：前向 + 反向

训练侧相对推理侧的核心新增是**完整反向**。长序列沿序列维切成 `chunk_size`（mcore 走 `mamba_chunk_size`、FSDP2 走 `gdn_chunk_size`；`gdn_chunk_size` 默认 64，`mamba_chunk_size` argparse 默认 256 ，需由当前配置显式选择）的块：块内用矩阵形式并行求解（WY/UT 变换 + 下三角求逆），块间沿 `last_recurrent_state` 递推。`ChunkGatedDeltaRuleFunction` 是 `torch.autograd.Function`，前向 `save_for_backward(q, q_rstd, k, k_rstd, v, g, beta, A, initial_state, cu_seqlens)`，反向一次返回 `dq/dk/dv/db/dg/dh0`。

前向 `chunk_gated_delta_rule_fwd` 的算子链（块内并行 + 块间状态递推）：

- `chunk_local_cumsum(g)` — 块内 forget gate 累加；
- `chunk_scaled_dot_kkt_fwd` — 算块内 `K·Kᵀ`（按 `beta`、`g` 加权）得下三角矩阵 `A`；
- `solve_tril(A)` — 按前一步尚未取负的 A 解 `(I+A)⁻¹`；torch 参考里的 attn 已取负号，不能混用符号，得 WY 表示的变换矩阵；
- `recompute_w_u_fwd` — 由 `A` 重建 `w, u`（`u` 即新的 value）；
- `chunk_gated_delta_rule_fwd_h` — 沿 chunk 递推状态 `h`，产 `v_new` 与 `final_state`（块间的递推发生在此）；
- `chunk_fwd_o` — 由 `q, k, v_new, h, g` 算输出 `o`。

反向 `chunk_gated_delta_rule_bwd` 重算 `w,u,h,v_new` 后，依次 `chunk_bwd_dv_local → chunk_gated_delta_rule_bwd_dhu(dh, dh0, dv) → chunk_bwd_dqkwg(dq, dk, dw, dg) → prepare_wy_repr_bwd(dk2, dv, db, dg2)`，累加 `dk += dk2 / dg += dg2`，最后对 `dg` 做 `reverse=True` 的 `chunk_local_cumsum` 反向累加；`use_qk_l2norm_in_kernel` 时 `dq/dk` 再过 `l2norm_bwd`。算子约束：仅 bf16（`q.dtype == float32` 直接报错）、`beta` 须 `[B, T, H]`、变长场景须 `cu_seqlens`（batch 必须为 1）。

三套后端共享上述 WY chunk 数学与同一套 autograd 签名，由参数选择（互斥校验见 `arguments.__post_init__`：`use_flash_gdn` 与 `use_triton_gdn` 不可同真）：

| 后端 | 触发 | 实现载体 |
| --- | --- | --- |
| `torch_chunk_gated_delta_rule` | 默认（两标志都不开） | 纯 PyTorch FP32 参考：`for i in range(1, chunk_size)` 前代法解块内下三角 + 块间状态 `for` 递推 |
| `chunk_gated_delta_rule` | `--use-triton-gdn` | MindSpeed core Triton 算子（`mindspeed.ops.triton.*`：`chunk_delta_h` / `chunk_o` / `solve_tril` / `wy_fast` / `cumsum`） |
| `flash_gated_delta_rule` | `--use-flash-gdn` | `fla_npu` AscendC 融合算子（`torch.ops.npu.npu_recompute_w_u_fwd` / `npu_chunk_gated_delta_rule_fwd_h` / `npu_chunk_fwd_o` / `npu_chunk_bwd_*` / `npu_prepare_wy_repr_bwd_*`），未编译安装则 `raise` |

Flash 后端的 forward/backward 在算子前后做 `transpose(1,2)` 把 `[B,T,H,*]` 调成 head-first 给 NPU 算子，并按 `prepare_chunk_indices(cu_seqlens, chunk_size)` 产块索引支持变长 TND。变长 actual_seq_len/cu_seqlens 需要选择支持它们的 Triton 或 Flash 后端；默认 torch_chunk_gated_delta_rule 在 cu_seqlens 非空时直接抛 NotImplementedError。三套后端的逐算子语义细节见 [gdn-chunk-kernels](../kernels/gdn_chunk_kernels.md)。

## 逐步递归形式（decode / 推理 cache）

`use_precomputed_states`（`seq_len == 1` 且带 cache）走递归路径 `torch_recurrent_gated_delta_rule`（FSDP2 路径优先用 `fla` 的 `fused_recurrent_gated_delta_rule`）：沿序列逐时间步串行扫描，每步对每个 head 的状态做

```
state ← state · exp(g_t)
kv_mem = Σ(state · k_t)
delta = (v_t − kv_mem) · β_t
state ← state + k_t ⊗ delta
out_t = (1/√K) · Σ(state · q_t)  # q_t 为未缩放查询
```

这是 chunk 形式 `chunk_size = 1` 的退化，状态逐步原地更新、无块内并行。decode 阶段的融合算子细节（推理侧）见 [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md)；训练前向用 chunk、decode/推理用递归，两者共享同一份 `A_log / dt_bias / conv1d / out_proj` 权重与门控公式。

## GDN 上下文并行（沿 head 而非沿序列）

GDN 的递推沿序列有严格的状态依赖，无法像标准 attention 那样把序列直接切给各 CP rank。`gdn_context_parallel.gdn_forward_with_cp` 的做法是把 **序列分片（CP layout）换成 head 分片（HP layout）** 再算：

1. `in_proj` 在 CP layout 下做（每 rank 持有自己的序列块、全部 head），拼 `qkvzba` 后 `transpose` 成 `[s, b, h]`；
2. `tensor_a2a_cp2hp` 全互换：`split_sections=[key_dim, key_dim, value_dim, value_dim, num_v_heads, num_v_heads]` 按 q/k/v/z/b/a 子组各自等比重排，换成 **全序列、head/cp** 布局；
3. `_undo_attention_load_balancing` 把 CP 的负载均衡交错序（如 `162534`）还原成顺序 `123456`，使递推看到正确时间序；
4. 在 HP layout 下走 conv1d（权重 `conv1d.weight`、`A_log`、`dt_bias` 都用 `get_parameter_local_cp` 按当前 CP rank 沿 head 切片）→ `chunk_gated_delta_rule`（本 rank 的 head 子集、全序列）→ `Qwen3NextRMSNormGated`；
5. `tensor_a2a_hp2cp` + `_redo_attention_load_balancing` 换回 CP layout（`123456 → 162534`），`out_proj` 在 CP layout 下输出。

变长场景由 `actual_seq_len` 取 `cu_seqlens`、`F.pad(..., (1,0))` 后转 TND（`rearrange(x, 'b s h d -> 1 (b s) h d')`）。`cp_size <= 1` 或 decode-cache 时回退原始 `_gdn_forward_original`。该替换在 CP 模板 `qwen3_next_gdn` 中注册（`context_parallel_mappings.py`）：把 `Qwen3NextGatedDeltaNet.forward` 换成 `gdn_forward_with_cp`，同时把同模型的 `flash_attention_forward` 换成标准 `context_parallel_attention_forward`——即混合模型里 **GDN 层走 head-parallel 全互换 CP、full-attention 层走常规序列 CP**。此能力仅 FSDP2 路径具备；mcore 路径 GDN 在 CP/TP>1 时直接断言报错。

## 当前实现与样例边界

mcore 的 Qwen3NextFeature 仍注册 full-attention-interval、linear-* 和 use-triton-gdn，Mamba feature 注册 mamba-chunk-size/mamba-d-conv；FSDP2 保留 gdn-chunk-size 与三套后端选择。参数存在不代表任意组合均有可执行 recipe。

当前树已无旧 examples/mcore/gated_deltanet 的 340M/1.3B 和旧 Qwen3-Next A3 启动脚本。该页据现存模块说明结构与并行边界，不再给出这些已删除脚本的启动配方或无法在当前来源核验的历史训练精度数字。新的完整训练配置需独立验证依赖、模型装配、正反向与精度。

## 当前实现的初始化细节

mcore GDN 在判断缓存分支前先将 `conv_state`、`recurrent_state` 初始化为 None，避免无既有状态时引用未赋值变量。FSDP2 混合模型的默认 RoPE 使用显式 `compute_default_rope_parameters`：从 `rope_parameters` 读取 theta/partial rotary factor，theta 缺省 10000；非 default 的 RoPE 类型从注册表按名称取。该调整属于同模型 full-attention 配套路径，不改变 GDN 的 Delta Rule 或其 TP/CP 限制。

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/README.md)（primary）
- [qwen3_next_gated_deltanet_attention.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/models/transformer/qwen3_next_gated_deltanet_attention.py)（supporting）
- [modeling_qwen3_next.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/fsdp2/models/qwen3_next/modeling_qwen3_next.py)（implementation）

## Links

- [gated-deltanet](../../../inference/concepts/modules/gated_deltanet.md)（跨域·推理：GDN 概念定义与推理侧 Prefill ChunkGDN / Decode RecurrentGDN，本页训练侧不重复概念、只补反向与 CP）
- [recurrent-gated-delta-rule](../../../inference/concepts/kernels/recurrent_gated_delta_rule.md)（跨域·推理：decode 逐步递归融合算子，本页递归形式的推理对照）
- [gdn-chunk-kernels](../kernels/gdn_chunk_kernels.md)（同域：chunk gated delta rule 三套后端的逐阶段算子细节）
- [deltanet-pretrain](../../guides/recipes/deltanet_pretrain.md)（同域·训练：Ascend-TLA 无门控纯 Delta Rule 预训练样例，与本页 Gated DeltaNet 同谱系对照）
- [mamba-ssm-train](mamba_ssm_train.md)（同为线性序列模型训练：Mamba 切序列 vs GDN 切 head）
