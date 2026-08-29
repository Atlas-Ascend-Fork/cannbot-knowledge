---
type: Concept
title: MHC 训练算子（DeepSeek-V4 Manifold-Constrained Hyper-Connections：Triton BMM + Sinkhorn）
description: MindSpeed-LLM deepseek4 把 DeepSeek-V4 的 MHC（Manifold-Constrained Hyper-Connections / 流形约束超连接 / 超连接）残差结构落到一组 Triton-on-Ascend 算子，补齐推理侧只有正向的 HcPre/HcPost 所缺的训练正反向。三条链：预连接 BMM（MhcPreBmm，4 路按 pre 权重融合为一路）；全量 Sinkhorn 切分（从 hc_fn 投影的 mixes 一次产 pre=σ+eps / post=2σ / comb，4×4 comb 经 Sinkhorn-Knopp 迭代逼近双随机，反向重放迭代逆传）；后连接 BMM（post_bmm1 Post 扩展 + post_bmm2 用 tle.extract_slice 做 comb 混合 + add → MHCPostTriton）。另有 pre_only 出口收敛（反向确定性归约避 atomic，配 MHCPreOnlyTriton：rms_norm+matmul+Triton 混编）与 mhc_recompute 省激活。全程 fp32、hc_mult=4 固定。与推理侧 mhc / mhc-hcpre-hcpost、torchtitan-npu npu_mhc_pre 对照。
tags:
- task.implementation
- topic.model_architecture
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/mhc.py
  role: supporting
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- agnostic
---

# MHC 训练算子（DeepSeek-V4 Manifold-Constrained Hyper-Connections：Triton BMM + Sinkhorn）

## Summary

MindSpeed-LLM 的 `deepseek4` 模型把 DeepSeek-V4 的 **MHC（Manifold-Constrained Hyper-Connections / 流形约束超连接）** 残差结构落到一组 [triton-on-ascend](../frameworks/triton_on_ascend.md) 融合算子上，补齐推理侧只有正向的 `HcPre`/`HcPost` 所缺的**训练正反向**。算子目录 `mindspeed_llm/tasks/models/transformer/deepseek4/mhc/` 下分三条计算链：

- **预连接 BMM**（`pre_bmm` → `MhcPreBmm`）：把 `num_stream=hc_mult=4` 路残差按 `pre` 权重加权求和为一路，送入子层的 `norm → Attention/MoE`。
- **全量 Sinkhorn 切分**（`sinkhorn_triton_kernel` → `sinkhorn`）：从 `hc_fn` 投影出的 `mixes` 一次产出 `pre`/`post`/`comb` 三组系数，其中 `comb`（4×4 残差混合矩阵）经 Sinkhorn-Knopp 迭代归一化。
- **后连接 BMM**（`post_bmm1` + `post_bmm2` + `add` → `MHCPostTriton`）：把子层一路输出经 `post` 扩展回 4 路、与经 `comb` 混合的多路残差逐元素相加，得到本子层的多路 MHC 输出。

另有 `pre_only`（网络出口只算 `pre` 的收敛路径，配 `MHCPreOnlyTriton`）与 `mhc_recompute`（按子层粒度丢弃/重算 MHC 激活省显存）。MHC 的结构语义（多路残差替代单残差、三类映射、Sinkhorn-Knopp 双随机约束）见跨域 [mhc](../../../inference/concepts/modules/mhc.md)，推理侧 AscendC/PyPTO 算子实现见 [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)；以下聚焦训练侧 Triton 算子各自的作用、相互配合与反向链路，不重述 mHC 概念定义。

整组算子全程 fp32 计算（输入 `x`、`mixes` 进核前 `.float()`，输出 `.to(dtype)` 回 bf16），`hc_scale`/`hc_base` 为 fp32 `nn.Parameter`；`hc_mult` 在 BMM 与 Sinkhorn 核内按 `4` 硬编码（`N != 4` 直接 `raise`），即 4 路超连接是这套核的固定形态。

## 多路残差与三阶段算子布局

`MHC(MegatronModule)` 持有 `hc_fn`（`LinearNoTP`，`[hc_mult·hidden → mix_hc]`，不切 TP）、`hc_base`（`[mix_hc]`）、`hc_scale`（`pre/post/comb` 三段用 `[3]`，出口 `head` 用 `[1]`）。`mix_hc = (2+hc_mult)·hc_mult`（pre/post 段）或 `hc_mult`（head 段）。进网络前单路 hidden 经 `hc_repeat`（`x.unsqueeze(2).repeat(1,1,hc_mult,1)`）扩成 4 路；每层 Attention、MoE 子层各做一轮 `hc_pre → 子层 → hc_post`；所有层结束由 `hc_head` 收敛回单路。`enable_mhc` 时连 PP 跨 stage 传的激活也带多路维——`get_tensor_shapes_in_mhc` 把 `(seq, mbs, hidden)` 换成 `(seq, mbs, hc_mult, hidden)`，`forward_backward_pipelining_with_interleaving_in_mhc` 据此收发。

三阶段在 `MHC` 内的 Triton/Native 双路由由 `use_triton_mhc` / `use_triton_sinkhorn` 控制：

| 阶段 | `MHC` 方法 | Triton 路径 | Native 基线 |
| ---- | ---- | ---- | ---- |
| 预连接 | `hc_pre` | RMSNorm-without-weight + `hc_fn` 投影 → `hc_split_sinkhorn_triton`（pre/post/comb）→ `MhcPreBmm` | `torch_hc_split_sinkhorn` + `sum(pre·x)` |
| 后连接 | `hc_post` | `MHCPostTriton` | `post·x + sum(comb·residual)` |
| 出口收敛 | `hc_head` | `MHCPreOnlyTriton` | rsqrt + `sigmoid(mixes·scale+base)+eps` + `sum(pre·x)` |

`torch_hc_split_sinkhorn` 是同文件内的 PyTorch 精度标杆，与 Triton 版逐步对齐，用于核验 Triton/TileLang 实现。

## 预连接 BMM（pre_bmm / MhcPreBmm）

`hc_pre_bmm_forward(H_pre[B,S,4], x[B,S,4,D]) → Y[B,S,D]`：把 4 路残差按预混合权重融合回一路。核 `hc_pre_bmm_fwd_kernel` 按 `4` 路展开——逐路 load 标量 `h_i` 与切片 `X_i`，`acc += h_i · X_i`，整个 `D` 维放进单个 `BLOCK_D=D` 的块、`GROUP=2` 个 `bs` 样本一组。

反向 `hc_pre_bmm_bwd_fused_kernel` 一核同出两路梯度：`dX_i = dY · h_i`（直接 store）；`dH_i = sum_d(X_i · dY)` 在 `D` 维分块累加，跨 `D` tile 用 `tl.atomic_add` 汇到 `dH[bs,i]`。`MhcPreBmm` 把正反向封进 `torch.autograd.Function`，在 `hc_pre` 内仅承担「pre 权重 × 多路」这一步 BMM，RMSNorm 与系数计算留在外层。

## 全量 Sinkhorn 切分（sinkhorn_triton_kernel / sinkhorn）

`hc_split_sinkhorn(mixes[B,S,(2+hc)·hc], hc_scale[3], hc_base) → (pre, post, comb)` 是 `hc_pre` 产 `pre/post/comb` 三系数的核心，两段 kernel：

`_hc_split_sinkhorn_kernel_part1` 把 `mixes` 沿尾维切成 `[hc, hc, hc·hc] = [4, 4, 16]` 三段（`GROUP=64`）：
- `pre = sigmoid(mixes_pre · scale[0] + base_pre) + eps`（一路加权用，`[B,S,4]`）
- `post = 2 · sigmoid(mixes_post · scale[1] + base_post)`（后扩展用，含 ×2 缩放，`[B,S,4]`）
- `comb = mixes_comb · scale[2] + base_comb`（4×4 混合矩阵的 logits，先不归一化）

`_hc_split_sinkhorn_kernel_part2` 对 `comb` 做 Sinkhorn-Knopp（`GROUP=32`）：4×4 矩阵先 `F.pad` 到 `[4, BLOCK_ALIGN=8]`、填充列置 `-inf`（保证 NPU 对齐访存且填充列 `exp→0` 不污染归约），减 `row_max` 后 `exp`，再做 `hc_sinkhorn_iters`（默认 20）轮交替归一——每轮先按行（`axis=2`，8 列）除以行和、再按列（`axis=1`，4 行）除以列和，逼近双随机矩阵；最后切回 `[:,:,:,:hc_mult]` 还原 4×4。双随机约束的语义见 [mhc](../../../inference/concepts/modules/mhc.md)。

反向 `hc_split_sinkhorn_backward` 同样两段。`part1` 反传 `pre`/`post` 的 sigmoid 雅可比（`pre` 用 `σ(1−σ)`、`post` 用 `2σ(1−σ)`），向 `grad_mixes` 对应段 store、`grad_hc_scale[0..1]`/`grad_hc_base` 段做 `atomic_add`。`part2` 先**重放**正向 Sinkhorn 迭代、把每轮 `row_sum`/`col_sum` 用 Ascend 扩展原语 `extension.insert_slice` 存进列表，再逆序 `extract_slice` 取出、逐轮反传行/列归一化的除法雅可比（`grad_direct − sum(...)` 形式），最后过 `exp`、`row_max` 减法（按 `max_mask/max_count` 均摊重复最大值）与线性变换，`atomic_add` 到 `grad_hc_scale[2]`/`grad_hc_base` 的 comb 段。

`sinkhorn.py` 的 `HcSplitSinkhornFunction` 把上述正反向封进 `torch.autograd.Function`，带 `@input_guard`/`@autocast_custom_fwd|bwd`（复用 [triton-on-ascend](../frameworks/triton_on_ascend.md) 核 `mindspeed/lite/ops/triton/utils.py`），外层包装 `hc_split_sinkhorn_triton` 标 `@torch.compiler.disable` 避免被 `torch.compile` 抓进图。

## 后连接 BMM（post_bmm1 + post_bmm2 + add / MHCPostTriton）

`MHCPostTriton` 把后连接拆成两段 BMM 加一次逐元素相加：

`hc_post_bmm1_forward(h_out[B,S,C], H_post[B,S,4]) → [B,S,4,C]` 是 **Post Mapping（一路扩展回 4 路）**：`y[bs,i,c] = h_out[bs,c] · H_post[bs,i]`，逐路 store。反向 `hc_post_bmm1_bwd_fused_kernel2` 在单核内顺序累加 `dh_out = Σ_i dy_i · hp_i`、并对 `dH_post_i = sum_c(dy_i · h_out)` 按 `C` 分块 `atomic_add`（`BLOCK_C` 上限 4096）。

`hc_post_bmm2_forward(H_res[B,S,4,4], x[B,S,4,C]) → [B,S,4,C]` 是 **Res(comb) Mapping（4×4 残差混合）**：`y[bs,i,c] = Σ_k H_res[bs,i,k] · x[bs,k,c]`。核心技巧是用 Ascend 扩展原语 `tle.extract_slice` 把 4×4 的每个标量逐列抽出、再 `tl.fma` 累加，避开 NPU 上低效的小粒度动态 gather（该写法与 [triton-on-ascend](../frameworks/triton_on_ascend.md) 描述的 `post_bmm2` 一致）。反向分两核：`hc_post_bmm2_bwd_dx_kernel` 用 `H_res^T` 算 `dX`；`hc_post_bmm2_bwd_dh_kernel` 把 16 个 `dH[i,k] = sum_c(dy_i · x_k)` 标量在 `C` 维归约后 `atomic_add`。

`MHCPostTriton.forward` 先把 `h_res.permute(0,1,3,2)`（转置 comb），分别跑 `bmm1(x, h_post)` 与 `bmm2(h_res, residual)`，再用 `add.py` 的 `add_fwd`（逐元素 `C=A+B` Triton 核，按行块发射、核内循环列块；wrapper 要求输入连续）把两路相加成 `[B,S,4,D]` 多路输出。反向对应调 `hc_post_bmm1_backward` + `hc_post_bmm2_backward`，把 `grad_h_res` 再 `permute` 回去。入参带 `recompute_info` 时把 `(x, residual, h_post, h_res)` `save_for_backward` 供重算。

## 仅预路径与网络出口收敛（pre_only / MHCPreOnlyTriton）

网络出口的 `hc_head` 只需把多路收敛回一路，不产 `post`/`comb`，故走更轻的 `pre_only`：`hc_pre_only_fwd` 只算 `pre = sigmoid(mixes · scale[0] + base) + eps`（`GROUP=48`，无 Sinkhorn 迭代）。它的反向刻意做**两阶段确定性归约**——主核 `hc_split_sinkhorn_backward_preonly_kernel` 把每个 program 的 `grad_hc_scale`/`grad_hc_base` 贡献写进临时 buffer（不用 `atomic_add`），再由单 program 的 `reduce_preonly_tmp_grads_kernel` 串行累加，规避 NPU 上原子加的非确定性。

`MHCPreOnlyTriton` 是 `hc_head` 的全融合 autograd：`torch_npu.npu_rms_norm`（`mhc_use_gamma=False`，即无 weight 的 RMSNorm）→ `matmul` 投影 → `hc_pre_only_fwd` → `hc_pre_bmm_forward`，是 Triton 核与 `torch_npu` 融合算子混编的典型；反向以 `torch_npu.npu_rms_norm_backward` + `hc_pre_only_bwd` + `hc_pre_bmm_backward` 回传 `grad_x/grad_weight/grad_branch_alpha/grad_branch_beta/grad_gamma`，并把 BMM 直传的 `grad_x_direct` 与 RMSNorm 链路的 `grad_x_rms` 相加得最终 `grad_x`。这套 `MhcPreBmm`/`MHCPostTriton`/`MHCPreOnlyTriton` 与核心仓 `mindspeed/lite/ops/triton/mhc/mhc_triton.py` 同名同逻辑（MindSpeed-LLM 内置一份副本），区别在 MindSpeed-LLM 这份额外带全量 `hc_split_sinkhorn`（pre/post/comb），核心仓 lite 版的 sinkhorn 只覆盖 `pre_only` 子集（`pre_bmm`/`post_bmm1`/`post_bmm2`/`MHCPostTriton` 在 lite 仍齐备）。

## MHC 重计算（mhc_recompute）

`MHCRecomputeInfo` 按子层粒度做 MHC 激活的选择性重计算：正向保存 `h_pre`/`h_pre_out`/`hc_post_out` 等中间量的句柄，`drop_*` 用 `untyped_storage().resize_(0)` 把激活存储置空释放显存，`recompute_*` 在反向用 `hc_pre_bmm_forward` 或 `layer.attn_mhc`/`mlp_mhc`（post 阶段）重新生成，`copy_untyped_storage` 在保留张量元数据下回填存储。`RecomputeInputWrap`/`RecomputeOutputWrap` 两个 `autograd.Function` 把 `drop()`（正向出口释放）与 `recompute()`（反向入口重建）挂到计算图边界。它和整网的重计算策略协同省激活，与 [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md) 里 Vector 类算子重计算的优化方向同源。

## 与推理侧 mHC 的对照

训练侧系数与推理侧命名一一对应：训练 `pre`/`post`/`comb`(=`H_res`) 即推理 `HcPre`/`HcPost` 的 `pre`/`post`/`comb`，公式（`pre=σ+eps`、`post=2σ`、`comb` Sinkhorn 双随机）一致。差异在落地路径——推理侧 cann-recipes-infer 给的是 AscendC/PyPTO 正向融合算子（见 [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)），MindSpeed-LLM 这套则用 Triton-on-Ascend + `torch_npu` 实现训练正反向。它与 torchtitan-npu 的 `npu_mhc_pre`/`npu_mhc_post` ModelConverter（950 走 `torch_npu.npu_hc_pre`+`npu_mhc_pre_sinkhorn_grad` 融合反向、非 950 走 `MHCPreTriton`/`MHCPostTriton`）是**两套并列的训练实现**，分属 MindSpeed-LLM 与 torchtitan-npu 两个框架，后者承载于 [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)。Sinkhorn 归一化的首步顺序在两侧略有差别（训练这份在 `exp(x−row_max)` 后做满 `iters` 轮「行→列」，推理 Native 首轮以 `softmax(-1)` 表达行归一），但都收敛到同一双随机流形，理论细节归 [mhc](../../../inference/concepts/modules/mhc.md)。

## Evidence

- [mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM) — MindSpeed-LLM @183e02c
  - [`mindspeed_llm/tasks/models/transformer/deepseek4/mhc/mhc.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/mhc.py)（`MHC` 模块 `hc_pre`/`hc_post`/`hc_head` 三阶段 + Triton/Native 双路由、`hc_fn`(LinearNoTP)/`hc_base`/`hc_scale`、`hc_repeat` 多路扩展、`torch_hc_split_sinkhorn` 精度标杆、`get_tensor_shapes_in_mhc` PP 携多路维）
  - [`mhc/pre_bmm.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/pre_bmm.py)（`hc_pre_bmm_forward/backward`：4 路 `acc+=h_i·X_i`、反向 `dX_i=dY·h_i` + `dH_i` 跨 D-tile `atomic_add`）
  - [`mhc/sinkhorn_triton_kernel.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/sinkhorn_triton_kernel.py)（`hc_split_sinkhorn`：part1 切 `[4,4,16]` 算 `pre=σ+eps`/`post=2σ`/`comb` logits、part2 pad `BLOCK_ALIGN=8`+`-inf`、`exp(x−row_max)`+`iters` 轮行/列归一；`hc_split_sinkhorn_backward` 重放迭代 + `extension.insert_slice/extract_slice` 逆传）
  - [`mhc/sinkhorn.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/sinkhorn.py)（`HcSplitSinkhornFunction` autograd + `@input_guard`/`@autocast_custom_*`、`hc_split_sinkhorn_triton` 标 `@torch.compiler.disable`）
  - [`mhc/post_bmm1.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/post_bmm1.py)（`hc_post_bmm1_forward` Post 扩展 `y[i,c]=h_out·H_post[i]`、`bwd_fused_kernel2` 顺序累加 `dh_out` + `dH_post` 按 C-tile `atomic_add`、`MhcPostBmm`）
  - [`mhc/post_bmm2.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/post_bmm2.py)（`hc_post_bmm2_forward` 4×4 comb 混合用 `tle.extract_slice`+`tl.fma` 逐列拆 bmm、反向 `bwd_dx`(H^T) / `bwd_dh`(C 维归约 16 标量 `atomic_add`)）
  - [`mhc/add.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/add.py)（`add_fwd`：逐元素 `C=A+B` 行块循环列块、合 bmm1/bmm2 多路输出）
  - [`mhc/pre_only.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/pre_only.py)（`hc_pre_only_fwd` 仅 `pre=σ(mixes·scale+base)+eps`、反向两阶段确定性归约 `reduce_preonly_tmp_grads_kernel` 避 atomic）
  - [`mhc/mhc_triton.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/mhc_triton.py)（`MhcPreBmm` / `MHCPostTriton`(`bmm1`+`bmm2`+`add_fwd`) / `MHCPreOnlyTriton`(`npu_rms_norm`+matmul+`hc_pre_only_fwd`+`hc_pre_bmm_forward`，Triton×`torch_npu` 混编)）
  - [`mhc/mhc_recompute.py`](https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/models/transformer/deepseek4/mhc/mhc_recompute.py)（`MHCRecomputeInfo` 子层粒度 `drop`/`recompute`、`copy_untyped_storage`、`RecomputeInput/OutputWrap` 图边界）
- [mindspeed](https://gitcode.com/ascend/MindSpeed) — MindSpeed core @1432cb0：[`mindspeed/lite/ops/triton/mhc/mhc_triton.py`](https://gitcode.com/Ascend/MindSpeed/blob/1432cb092818b870c31b61db0eb6d3378b7fbdad/mindspeed/lite/ops/triton/mhc/mhc_triton.py)（同名 `MHCPreOnlyTriton`/`MHCPostTriton`，lite 版仅 `pre_only` 子集、无全量 `hc_split_sinkhorn`）；`hc_split_sinkhorn` 复用 lite `utils.py` 的 `input_guard`/`autocast_custom_*`
- 论文：[Manifold-Constrained Hyper-Connections (Xie et al., 2026)](https://arxiv.org/abs/2512.24880)（mHC 命名与流形约束来源）

## Links

- [mhc](../../../inference/concepts/modules/mhc.md)（跨域：mHC 多路残差 / 三映射 / Sinkhorn-Knopp 结构语义，训练侧 pre/post/comb 系数公式的概念出处）
- [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)（跨域：推理侧 HcPre/HcPost AscendC/PyPTO 正向融合算子，与训练侧 Triton 正反向对照）
- [triton-on-ascend](../frameworks/triton_on_ascend.md)（本算子族所属的昇腾 Triton 算子后端，lite `utils.py` 装饰器与 `tle.extract_slice` 扩展原语来源）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（跨框架对照：torchtitan-npu `npu_mhc_pre`/`npu_mhc_post` converter 的另一套 V4 mHC 训练实现）

<!-- cannbot:related:start -->
## 相关

- [HcPre / HcPost (mHC 融合算子)](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)（`related`）：补齐推理侧只有正向的 `HcPre`/`HcPost` 所缺的**训练正反向**。；`HcPre`（多路 → 一路）**：融合 RMSNorm → `mixes = linear(x, hc_fn)·rsqrt` → Sinkhorn-Knopp 三段切分 → 用 Pre 系数把多路残差加权求和为一路，同时输出 `post` / `comb` 系数透传给 `HcPost`。。训练卡补齐 HcPre/HcPost 的反向与 Triton BMM/Sinkhorn 链，推理 kernel 卡闭合成对正向融合算子的输入输出与流水；二者可对照验证前向合同和梯度实现。
- [Triton-on-Ascend（昇腾 Triton 算子后端）](../frameworks/triton_on_ascend.md)（`related`）：“轻量 `mindspeed/lite/ops/triton/`（MHC 超连接 bmm + Sinkhorn 路由 + MoE permute sort）”；“MindSpeed-LLM 的 `deepseek4` 模型把 DeepSeek-V4 的 **MHC（Manifold-Constrained Hyper-Connections / 流形约束超连接）** 残差结构落到一组 ［triton-on-ascend］(../frameworks/triton_on_ascend.md) 融合算子上”。框架卡定位 lite Triton 目录的 MHC 算子族，kernel 卡确认 DeepSeek-V4 MHC 训练链由该后端融合算子实现。
- [mHC (Manifold-Constrained Hyper-Connections)](../../../inference/concepts/modules/mhc.md)（`same_topic`）：推理概念卡说明“mHC 把残差扩展为 `hc_mult` 路”；训练实现卡明确“训练侧系数与推理侧命名一一对应：训练 `pre`/`post`/`comb`(=`H_res`) 即推理 `HcPre`/`HcPost` 的 `pre`/`post`/`comb`，公式（`pre=σ+eps`、`post=2σ`、`comb` Sinkhorn 双随机）一致。”，两端描述的是同一 mHC 多路残差与 Pre/Post/comb 数学对象，只是分别覆盖推理结构语义和训练正反向实现。
<!-- cannbot:related:end -->
