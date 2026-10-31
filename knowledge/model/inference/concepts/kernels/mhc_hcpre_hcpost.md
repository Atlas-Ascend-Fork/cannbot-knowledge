---
type: Concept
title: HcPre / HcPost (mHC 融合算子)
description: '`HcPre` 与 `HcPost` 是 DeepSeek-V4 mHC 残差结构的成对融合算子，完成 Attention/MoE 子层前后的多路↔单路变换。HcPre 融合 RMSNorm、hc_fn 线性变换、Sinkhorn-Knopp 和 pre 加权求和，输出 y、post、comb；HcPost 用 post 扩展子层输出并与 comb 残差合并，目标是让中间数据留在 UBuffer。A3 AscendC 采用 Cube:Vector=1:2 流水，Decode 切 K、Prefill 切 token；PyPTO 以 MPMD 并行 Vector RMSNorm 与 Cube MatMul，并用 split-K 和静态展开。VF 的历史测量另见来源观测。Native 与 PyPTO 的首轮 Sinkhorn 均先行归一再列归一，数值实现细节以各自代码为准。'
tags:
- task.implementation
- topic.model_architecture
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_mHC_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/op_impls/mhc.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto_python/impl/hc_pre_pypto.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a3
- '950'
---
# HcPre / HcPost (mHC 融合算子)

## Summary

`HcPre` 与 `HcPost` 是 DeepSeek-V4 为 **mHC（Manifold-Constrained Hyper-Connections）** 残差结构发布的两个全新融合算子，承载 [mhc](../modules/mhc.md) 在每层 Attention / MoE 子层前后的多路↔单路残差转换计算：

- **`HcPre`（多路 → 一路）**：融合 RMSNorm → `mixes = linear(x, hc_fn)·rsqrt` → Sinkhorn-Knopp 三段切分 → 用 Pre 系数把多路残差加权求和为一路，同时输出 `post` / `comb` 系数透传给 `HcPost`。整套流程融为单算子、通过一个接口暴露给脚本，极致优化产生的中间过程脚本侧不感知。
- **`HcPost`（一路输出 → 多路 + 残差融合）**：把子层一路输出经 Post 扩展回多路，与经 `comb` 混合的多路残差加和。融合的核心价值是**消除小算子下的内存墙**——数据不出核内 buffer（UBuffer）即完成计算，大幅减少 HBM 访存。

这里聚焦**算子实现层面**（A3 分离架构 CV 流水、Decode/Prefill 双模板、Tiling、性能、PyPTO 实现技巧）。mHC 的结构语义、三类映射作用、Sinkhorn-Knopp 双随机约束的计算公式见 [mhc](../modules/mhc.md)。算子在 V4 整模型中的位置见 [deepseek-v4](../models/deepseek_v4.md)。

当前hc_pre注册native、hc_pre_ascendc、hc_pre_ascendc_a3和hc_pre_pypto_a3；hc_post仍为native/hc_post_ascendc。A3专用入口延迟import custom_ops，调用torch.ops.custom.npu_hc_pre；通用AscendC入口已改用cann_ops_transformer.mhc_pre_sinkhorn，Post改为cann_ops_transformer.mhc_post(residual, comb, x, post)，不能继续复制旧custom.npu_hc_post参数顺序。

当前V4按packed token保留[T,hc_mult,H]残差；hc_pre_ascendc wrapper先unsqueeze(1)，接融合算子的8项返回，仅选y/post/comb并把comb末维unflatten，再squeeze回packed。下方Native/PyPTO形状是各自参考接口，不能把一种wrapper的rank约定套给另一种。

## 接口契约

| 算子 | 入参 | 产出 |
| ---- | ---- | ---- |
| `hc_pre(x, hc_fn, hc_scale, hc_base, hc_mult, hc_sinkhorn_iters, norm_eps, hc_eps)` | `x [b,s,hc_mult,d]` 多路残差、混合权重 `hc_fn [mix_hc, hc_mult·d]`、`hc_scale [3]`、`hc_base [mix_hc]` | `(y [b,s,d], post [b,s,hc_mult], comb [b,s,hc_mult,hc_mult])` |
| `hc_post(x, residual, post, comb)` | 子层一路输出 `x`、原多路 `residual`、`HcPre` 透传的 `post` / `comb` | `y [b,s,hc_mult,d]`（多路 mHC 输出） |

固定 PyPTO 生产路径的 epsilon 限制：hc_pre_pypto_a3 不向下传 norm_eps，hc_pre_kernel 实际用 hc_eps 调 rms_norm_denom；Native 则使用 norm_eps。两者不同值时归一化语义不同，不能将接口里的 norm_eps 当作 PyPTO 已生效的参数；切换实现前须核对并对齐精度。

`mix_hc = (hc_mult + 2)·hc_mult`。每层调两轮 `hc_pre → 子层 → hc_post`（Attention 用 `hc_attn_*`，MoE/FFN 用 `hc_ffn_*`）。PyPTO 参考实现中权重 dtype 为 `x: bf16`、`hc_fn/hc_scale/hc_base: fp32`，且断言 `d == 4096`、`hc_mult == 4`（见 `hc_pre_pypto.py:check_input_output_shape_dtype`）。

## A3 分离架构与 CV 流水

A3 为**分离架构**：Cube 核与 Vector 核数比为 1:2，1 个 Cube 核 + 2 个 Vector 核构成一个 AICore 组核；L1/L0A/L0B/L0C 为 Cube 片上 Buffer，UB 为 Vector 片上 Buffer。CV 之间的数据交换需借助 HBM（workspace）。算子据此组织 **CV 流水并行**：把 Cube 计算（`x @ hc_fn` 矩阵乘）与 Vector 计算（RMSNorm 分母、Sinkhorn 的归约/逐元素乘除）在时间轴上重叠以掩盖开销。

## HcPre AscendC 实现：Decode 切 K / Prefill 分 token 双模板

A3 上 `HcPre` 按不同 shape 的 Tiling 差异实现**两个模板**：

### Decode 场景模板（多核切 K）

Decode 场景 m（token 数）较小，故在 **K 轴上做多核切分**提升性能：

- **阶段一**：搬运 → 类型转换 → Cube 计算形成 CV 流水，中间内存较小、基本 L2 命中，提升流水效率。
- **阶段二**：提前搬运 `x`，掩盖 `pre`、`post`、`combine` 的 Vector 计算开销。

来源 shape 扫描统一见[A3 LI/HcPost 来源观测](../../optimizations/benchmark_observations/ascendc_a3_li_hcpost_source_observations.md)；不在机制卡重复维护性能表。

## PyPTO 实现（hc_pre / hc_post）

PyPTO 以较少代码量（`hc_pre` 约 0.4 KLOC）实现 `hc_pre`，该固定单 die 工作负载的测量统一见[PyPTO V4 待核验观测](../../optimizations/benchmark_observations/pypto_v4_operator_source_observations.md)。关键技巧（实现见 `ops/pypto_python/impl/hc_pre_pypto.py`）：

- **MPMD 流水并行**：计算流程第一步是 Vector 计算（RMSNorm 分母）、第二步 `x @ hc_fn` 是 Cube 矩阵乘，二者无依赖。PyPTO 框架支持两任务同时执行，无需手动插入同步。
- **指令优化（免显式广播）**：Sinkhorn-Knopp 涉及大量重复的归约串联逐元素乘除；通过 pass 优化与 PTO 指令（`set_operation_config(combine_axis=True)`）避免显式广播，实现高性能逐元素计算。
- **Decode 切 K MatMul**：Decode 下 matmul 的 K 轴很长（16K）、M/N 轴较小，采用切 K 把数据切到不同核充分利用算力——代码以 `enable_split_k=True` + `enable_multi_data_load` 配 `set_cube_tile_shapes`。
- **Prefill 转置技巧（guide/test 示例路径）**：Prefill 的 `t`（0 轴）通常较大，而 Sinkhorn-Knopp 归约轴很小（`hc_mult=4`）。采用数学等价的转置技巧，在矩阵乘中直接算 `hc_fn^T @ x^T`（代码 `hc_pre_kernel_prefill` 用 `matmul(hc_fn, x_fp32, b_trans=True)` 产 `(mix_hc, t)`），使 `t` 置于尾轴、归约轴变为 -2/-3 轴，提高计算效率。注意 `hc_pre_kernel_prefill` 在仓内仅由 `test_hc_pre_pypto.py` 调用，是 guide / test 示例路径；PyPTO 的生产入口是 `hc_pre_kernel`（见下条）。
- **生产入口与 Unrollist 动态转静态**：PyPTO 生产入口为 `hc_pre_kernel`（`hc_pre_pypto.py:132`，被生产 wrapper 在 `:402` 调用；用 `matmul(x_fp32, hc_fn, b_trans=True)` + `enable_split_k`），其 `unroll_list=[256, 64, 16, 4, 1]` 对动态值 `t` 多分档 + 静态 Tile 切分以适应不同 `t`。示例路径 `hc_pre_kernel_prefill` 则用 `unroll_list=[128, 1]`。这一"动态值多分档 + 静态 Tile 切分"思路使 Prefill/Decode 的 `t` 差异（一套切分难以两端兼优）在各场景均达较优性能。

`hc_post` 在仓内**只有 Native 与 AscendC 两版实现，没有 PyPTO 版**（`mhc.py` 仅注册 `hc_post`(native) 与 `hc_post_ascendc`，且 `ops/pypto_python` 内无 `hc_post` 注册；代码注释明确 "hc_post currently support Native and AscendC version"）。PyPTO guide 中关于 `hc_post` 计算式 `y = post·x + sum(comb·residual)`、以及毕昇 PTO 编译器 VF 自动融合相比未使能提升 **来源观测中的相对值** 的论述，描述的是 PTO-ISA / VF 融合能力本身（"PTO-ISA 跨 A2/A3/950D 代际兼容、兼容不降速"），而非仓内已落地的 `hc_post` PyPTO 算子。框架语义见 [pypto](../frameworks/pypto.md)。

> Sinkhorn-Knopp 归一化顺序（PyPTO guide L190「每次迭代先逐行归一化再逐列归一化」；mHC guide 未展开此算法）：三路代码首步**一致**，均先行归一再列归一、再进入 iters-1 轮行(-1)→列(-2)交替——Native（`mhc.py:44-51`）首次行归一用 `softmax(-1)`+eps、PyPTO（`hc_pre_pypto.py:51-57`）用数值稳定 `exp(x − row_max) / row_sum`、TileLang（`hc_split_sinkhorn_kernel.py:114-119`）reduce_max→sub→exp→reduce_sum，三者数学等价且与文档「先行后列」一致（softmax(-1) 即首轮行归一，**无首步顺序差异**）。详细公式见 [mhc](../modules/mhc.md)。

## 共享 / 复用关系

mHC `HcPre` / `HcPost` 的分核**基于 shape 即可确定（非值依赖）**：mHC guide 全文未出现 AICPU / Scheduler，源文档也未披露这两个算子使用 AICPU Scheduler。因此本算子**不与 AICPU Scheduler 关联**——值依赖分核下沉机制仅适用于 SparseAttnSharedKV / LightningIndexer 这类需运行时上下文长度的算子，与 mHC 无关。`hc_head`（离开网络时多路收敛回单路）在代码 `modeling_deepseek.py` 内以 `HcPre` 风格的 Pre 融合实现（只输出 `y`），属同结构的脚本侧函数，源未将其单独发布为融合算子。

## 训练侧入口

当前torchtitan-npu已改用override/ops机制；旧ModelConverter和npu_mhc_pre/post默认列表已删除，不能作为启用配方。训练的pre/post/head replacement、后端及反向边界由[融合组件入口](../../../training/concepts/frameworks/npu_fused_op_converters.md)和[mHC训练](../../../training/concepts/kernels/mhc_train.md)维护，不能把推理的注册键直接当训练配置。

## Evidence

- [deepseek_v4_mHC_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_mHC_guide.md)（primary）
- [mhc.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/op_impls/mhc.py)（implementation）
- [hc_pre_pypto.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto_python/impl/hc_pre_pypto.py)（implementation）
- [deepseek_v4_pypto_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md)（implementation）

## Links

- [mhc](../modules/mhc.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [pypto](../frameworks/pypto.md)（HcPre 的 PyPTO 实现）
- [ascendc](../frameworks/ascendc.md)（HcPre / HcPost 的 AscendC 实现）
- [autofuse](../frameworks/autofuse.md)（`hc_post` 经 `@torch.compile` 自动融合的并列路径，A3 实测 4x）

运行于 Atlas A3（arch_support 已覆盖 A3 / ascend-950）。
- [deepseek-v4-continue-pretrain](../../../training/guides/recipes/deepseek_v4_continue_pretrain.md)（跨域·训练：mHC 在 V4 训练侧(AutoFuse 融合小算子)）
- [mhc-train](../../../training/concepts/kernels/mhc_train.md)（跨域·训练：MindSpeed-LLM 的 mHC 训练正反向 Triton BMM + Sinkhorn 算子，与本页 AscendC 正向算子对照）
