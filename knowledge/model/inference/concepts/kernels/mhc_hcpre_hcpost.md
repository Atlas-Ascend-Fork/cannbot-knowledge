---
type: Concept
title: HcPre / HcPost (mHC 融合算子)
description: '`HcPre` 与 `HcPost` 是 DeepSeek-V4 mHC 残差结构的成对融合算子，完成 Attention/MoE 子层前后的多路↔单路变换。HcPre 融合 RMSNorm、hc_fn 线性变换、Sinkhorn-Knopp 和 pre 加权求和，输出 y、post、comb；HcPost 用 post 扩展子层输出并与 comb 残差合并，目标是让中间数据留在 UBuffer。A3 AscendC 采用 Cube:Vector=1:2 流水，Decode 切 K、Prefill 切 token；PyPTO 以 MPMD 并行 Vector RMSNorm 与 Cube MatMul，并用 split-K 和静态展开。hc_post 的 VF 报告提升 22.7%。Native 与 PyPTO 的首轮 Sinkhorn 归一顺序不同，应以各自代码为准。'
tags:
- task.implementation
- topic.model_architecture
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_mHC_guide.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: supporting
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md
  role: supporting
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
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

代码侧 `hc_pre` 注册三版实现（`func_key`：`native` / `hc_pre_ascendc` / `hc_pre_pypto_a3`），`hc_post` 注册两版（`native` / `hc_post_ascendc`）；AscendC 入口 `torch.ops.custom.npu_hc_pre` / `torch.ops.custom.npu_hc_post`。

## 接口契约

| 算子 | 入参 | 产出 |
| ---- | ---- | ---- |
| `hc_pre(x, hc_fn, hc_scale, hc_base, hc_mult, hc_sinkhorn_iters, norm_eps, hc_eps)` | `x [b,s,hc_mult,d]` 多路残差、混合权重 `hc_fn [mix_hc, hc_mult·d]`、`hc_scale [3]`、`hc_base [mix_hc]` | `(y [b,s,d], post [b,s,hc_mult], comb [b,s,hc_mult,hc_mult])` |
| `hc_post(x, residual, post, comb)` | 子层一路输出 `x`、原多路 `residual`、`HcPre` 透传的 `post` / `comb` | `y [b,s,hc_mult,d]`（多路 mHC 输出） |

`mix_hc = (hc_mult + 2)·hc_mult`。每层调两轮 `hc_pre → 子层 → hc_post`（Attention 用 `hc_attn_*`，MoE/FFN 用 `hc_ffn_*`）。PyPTO 参考实现中权重 dtype 为 `x: bf16`、`hc_fn/hc_scale/hc_base: fp32`，且断言 `d == 4096`、`hc_mult == 4`（见 `hc_pre_pypto.py:check_input_output_shape_dtype`）。

## A3 分离架构与 CV 流水

A3 为**分离架构**：Cube 核与 Vector 核数比为 1:2，1 个 Cube 核 + 2 个 Vector 核构成一个 AICore 组核；L1/L0A/L0B/L0C 为 Cube 片上 Buffer，UB 为 Vector 片上 Buffer。CV 之间的数据交换需借助 HBM（workspace）。算子据此组织 **CV 流水并行**：把 Cube 计算（`x @ hc_fn` 矩阵乘）与 Vector 计算（RMSNorm 分母、Sinkhorn 的归约/逐元素乘除）在时间轴上重叠以掩盖开销。

## HcPre AscendC 实现：Decode 切 K / Prefill 分 token 双模板

A3 上 `HcPre` 按不同 shape 的 Tiling 差异实现**两个模板**：

### Decode 场景模板（多核切 K）

Decode 场景 m（token 数）较小，故在 **K 轴上做多核切分**提升性能：

- **阶段一**：搬运 → 类型转换 → Cube 计算形成 CV 流水，中间内存较小、基本 L2 命中，提升流水效率。
- **阶段二**：提前搬运 `x`，掩盖 `pre`、`post`、`combine` 的 Vector 计算开销。

**性能（源文档实测，hc=4, d=4096）：**

| 规格 b·s | 性能 (us) |
| ---- | ---- |
| 16 | 32.8 |
| 32 | 37 |
| 64 | 44 |
| 128 | 60 |

### Prefill 场景模板（分 token）

Prefill 场景按 **token 进行分核**形成 CV 流水。当前实现中一阶段与二阶段的 Vector 计算**串行**执行；源文档列出后续优化方向：让两个 V 核分别承担一阶段、二阶段的 Vector 计算，流水执行进一步掩盖开销。

**性能（源文档实测，hc=4, d=4096）：**

| 规格 b·s | 性能 (us) |
| ---- | ---- |
| 4K | 1254.916 |
| 16K | 4784.204 |
| 64K | 18545.39 |

## HcPost AscendC 实现：消除内存墙

`HcPost` 在小算子下的瓶颈是内存墙；融合后 Vector 中间计算结果常驻 UBuffer（核内 buffer），减少 HBM 访存，极大提升性能。

Tiling：在 b、s、d 轴上分核，b、s 合并为 `bs` 轴，在 `(bs, d)` 上做 tile 块划分，每块大小 `(m, n)`。极小 case 多核切分时在启动开销与处理开销间权衡——每核最低搬运数据量 4KB、`n` 长度数据量不小于 1KB 且 512B 对齐。按 hc 轴 buffer 占用与流水掩盖的权衡分两类模板：

1. **hc 较小**：一次性把 `residual` 的 tile 块 `(m, hc, n)` 全部搬入；
2. **hc 泛化（UB 可能不够）**：在 `residual` 的 hc 轴上开循环流水，每次搬入 t 个。

**性能（源文档实测，hc=4, d=4096）：**

| 规格 b·s | 性能 (us) |
| 规格 b·s | 性能 (us) |
| ---- | ---- | --- | ---- | ---- |
| 8 | 5.09 |
| 128 | 13.85 |
| 16 | 5.37 |
| 4K | 319.86 |
| 32 | 6.99 |
| 16K | 1264.68 |
| 64 | 9.16 |
| 64K | 5044.53 |

## PyPTO 实现（hc_pre / hc_post）

PyPTO 以较少代码量（`hc_pre` 约 0.4 KLOC）实现 `hc_pre`，单 die、B=64、MTP1、S2=8K 场景下实测 70 us。关键技巧（实现见 `ops/pypto_python/impl/hc_pre_pypto.py`）：

- **MPMD 流水并行**：计算流程第一步是 Vector 计算（RMSNorm 分母）、第二步 `x @ hc_fn` 是 Cube 矩阵乘，二者无依赖。PyPTO 框架支持两任务同时执行，无需手动插入同步。
- **指令优化（免显式广播）**：Sinkhorn-Knopp 涉及大量重复的归约串联逐元素乘除；通过 pass 优化与 PTO 指令（`set_operation_config(combine_axis=True)`）避免显式广播，实现高性能逐元素计算。
- **Decode 切 K MatMul**：Decode 下 matmul 的 K 轴很长（16K）、M/N 轴较小，采用切 K 把数据切到不同核充分利用算力——代码以 `enable_split_k=True` + `enable_multi_data_load` 配 `set_cube_tile_shapes`。
- **Prefill 转置技巧（guide/test 示例路径）**：Prefill 的 `t`（0 轴）通常较大，而 Sinkhorn-Knopp 归约轴很小（`hc_mult=4`）。采用数学等价的转置技巧，在矩阵乘中直接算 `hc_fn^T @ x^T`（代码 `hc_pre_kernel_prefill` 用 `matmul(hc_fn, x_fp32, b_trans=True)` 产 `(mix_hc, t)`），使 `t` 置于尾轴、归约轴变为 -2/-3 轴，提高计算效率。注意 `hc_pre_kernel_prefill` 在仓内仅由 `test_hc_pre_pypto.py` 调用，是 guide / test 示例路径；PyPTO 的生产入口是 `hc_pre_kernel`（见下条）。
- **生产入口与 Unrollist 动态转静态**：PyPTO 生产入口为 `hc_pre_kernel`（`hc_pre_pypto.py:132`，被生产 wrapper 在 `:402` 调用；用 `matmul(x_fp32, hc_fn, b_trans=True)` + `enable_split_k`），其 `unroll_list=[256, 64, 16, 4, 1]` 对动态值 `t` 多分档 + 静态 Tile 切分以适应不同 `t`。示例路径 `hc_pre_kernel_prefill` 则用 `unroll_list=[128, 1]`。这一"动态值多分档 + 静态 Tile 切分"思路使 Prefill/Decode 的 `t` 差异（一套切分难以两端兼优）在各场景均达较优性能。

`hc_post` 在仓内**只有 Native 与 AscendC 两版实现，没有 PyPTO 版**（`mhc.py` 仅注册 `hc_post`(native) 与 `hc_post_ascendc`，且 `ops/pypto_python` 内无 `hc_post` 注册；代码注释明确 "hc_post currently support Native and AscendC version"）。PyPTO guide 中关于 `hc_post` 计算式 `y = post·x + sum(comb·residual)`、以及毕昇 PTO 编译器 VF 自动融合相比未使能提升 **22.7%** 的论述，描述的是 PTO-ISA / VF 融合能力本身（"PTO-ISA 跨 A2/A3/950D 代际兼容、兼容不降速"），而非仓内已落地的 `hc_post` PyPTO 算子。框架语义见 [pypto](../frameworks/pypto.md)。

> Sinkhorn-Knopp 归一化顺序（PyPTO guide L190「每次迭代先逐行归一化再逐列归一化」；mHC guide 未展开此算法）：三路代码首步**一致**，均先行归一再列归一、再进入 iters-1 轮行(-1)→列(-2)交替——Native（`mhc.py:44-51`）首次行归一用 `softmax(-1)`+eps、PyPTO（`hc_pre_pypto.py:51-57`）用数值稳定 `exp(x − row_max) / row_sum`、TileLang（`hc_split_sinkhorn_kernel.py:114-119`）reduce_max→sub→exp→reduce_sum，三者数学等价且与文档「先行后列」一致（softmax(-1) 即首轮行归一，**无首步顺序差异**）。详细公式见 [mhc](../modules/mhc.md)。

## 共享 / 复用关系

mHC `HcPre` / `HcPost` 的分核**基于 shape 即可确定（非值依赖）**：mHC guide 全文未出现 AICPU / Scheduler，源文档也未披露这两个算子使用 AICPU Scheduler。因此本算子**不与 AICPU Scheduler 关联**——值依赖分核下沉机制仅适用于 SparseAttnSharedKV / LightningIndexer 这类需运行时上下文长度的算子，与 mHC 无关。`hc_head`（离开网络时多路收敛回单路）在代码 `modeling_deepseek.py` 内以 `HcPre` 风格的 Pre 融合实现（只输出 `y`），属同结构的脚本侧函数，源未将其单独发布为融合算子。

## 在 torchtitan-npu 训练侧的应用（跨域 cann-train）

推理侧 `HcPre` / `HcPost` 是直接发布的融合算子；训练侧 [npu-fused-op-converters](../../../training/concepts/frameworks/npu_fused_op_converters.md) 把它们封装成两个 torchtitan **ModelConverter**，在 [deepseek-v4-continue-pretrain](../../../training/guides/recipes/deepseek_v4_continue_pretrain.md) 的 DeepSeek-V4 训练任务启动时，按硬件类型把模型里的 `HcPre` / `HcPost` 模块自动替换为 NPU 亲和实现（含**反向**）。converter 源码 `torchtitan_npu/converters/kernels/mhc_prepost.py`，按 `get_npu_device_type() == "A5"` 选实现。

### `npu_mhc_pre`（替换 `HcPre`，**默认开启**）

替换模型中的 `HcPre` 模块，做 mHC pre-processing（多路 → 一路 + Sinkhorn 系数透传）：

- **950（`NpuHcPreFused`）**：`convert()` 先 `import custom_ops` 注册 950 融合算子；前向走 `MHCPre.apply` → `torch_npu.npu_hc_pre(..., need_grad=True)`，`npu_hc_pre` 产出 8 元组 `(y, post, comb_frag, h_pre, hc_before_norm, inv_rms, sum_out, norm_out)`，`forward` 仅返回 `(y, post, comb_frag)`、其余 5 个中间量 `save_for_backward`；反向用专门的融合算子 `torch_npu.npu_mhc_pre_sinkhorn_grad(...)` 回传 `grad_x / grad_phi(权重) / grad_alpha(hc_scale) / grad_bias(hc_base)`。这是训练侧专有的 backward 融合，推理侧无反向。
- **非 950（`NpuHcPre`）**：走已有 Triton 实现 `MHCPreTriton.apply(...)`（前向把 4D `[B,S,N,D]` flatten 为 `[B,S,N*D]`，再 RMSNorm + 线性投影 + Sinkhorn-Knopp 聚合）。
- **默认状态**：在 DeepSeek-V4 的 `config_registry.py` `_default_converters()` 中**已默认启用**（与 `npu_rms_norm` / `npu_permute` / `npu_gmm` / `npu_rope` / `npu_smla` 并列）。

### `npu_mhc_post`（替换 `HcPost`，**默认不开**，且非 950 兼带替换 `HcHead`）

替换模型中的 `HcPost` 模块，做 mHC post-processing（一路输出扩展回多路 + `comb` 残差融合）：

- **950（`NpuHcPostFused`）**：前向 `torch_npu.npu_hc_post(x, residual, post, comb)`，反向 `torch_npu.npu_mhc_post_grad(...)` 回传 `grad_x / grad_residual / grad_h_post / grad_h_res`。
- **非 950（`NpuHcPost`）**：走 Triton `MHCPostTriton.apply(...)`；**且** `MHCPostConverter` 在 `not use_fused_kernel` 分支里**额外把 `HcHead` 替换为 `NpuHcHead`**（Triton `MHCPreOnlyTriton.apply(...)`，对应推理侧脚本里 Pre 风格只输出 `y` 的收敛函数 `hc_head`）。950 融合路径则不替换 `HcHead`。
- **默认状态**：在 `_default_converters()` 中**未打开**，只在 `_enable_all_converters()` 中出现。出于性能考虑——**950 上建议按需打开**以使用 MHC post 融合算子；**A3 上建议保持关闭**，继续走默认模型路径，避免 converter 替换带来的额外开销或性能退化。

> 与推理侧 `mhc.py` 三/两注册键（`native` / AscendC / PyPTO）对应关系：训练 converter 复用同一对 `torch_npu.npu_hc_pre` / `npu_hc_post` 算子（950），并各自补了 backward 融合算子（`npu_mhc_pre_sinkhorn_grad` / `npu_mhc_post_grad`）；非 950 下走 Triton，是训练侧独有的第三套实现路径。详见 [npu-fused-op-converters](../../../training/concepts/frameworks/npu_fused_op_converters.md)。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_mHC_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_mHC_guide.md)（frontmatter 主源：HcPre/HcPost 融合范围与价值、A3 分离架构 CV 流水、Decode 切 K / Prefill 分 token 双模板、Tiling 与流水、性能 us 表）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md)（hc_pre MPMD 流水、免广播指令优化、Decode 切 K、Prefill 转置技巧、Unrollist；hc_post VF 自动融合 +22.7%；hc_pre 实测 70 us / 0.4 KLOC）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modules/op_impls/mhc.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modules/op_impls/mhc.py)（`hc_pre` 三注册键 `native`/`hc_pre_ascendc`(`npu_hc_pre`)/`hc_pre_pypto_a3`；`hc_post` 两注册键 `native`/`hc_post_ascendc`(`npu_hc_post`)；接口产出 `(y, post, comb)` / `y`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/pypto_python/impl/hc_pre_pypto.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/ops/pypto_python/impl/hc_pre_pypto.py)（生产入口 `hc_pre_kernel`（`:132`，生产 wrapper 在 `:402` 调用）`matmul(x_fp32, hc_fn, b_trans=True)` + `enable_split_k` + `unroll_list=[256,64,16,4,1]`；`hc_pre_kernel_prefill`（`:249`）`matmul(hc_fn, x_fp32, b_trans=True)` 转置 + `unroll_list=[128,1]`，仅由 `example/test_hc_pre_pypto.py:224` 调用（guide/test 示例路径）；`ops/pypto_python` 内无 `hc_post` 注册；`set_operation_config(combine_axis=True)`；`hc_split_sinkhorn` 首步行归一→列归一）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modeling_deepseek.py)（`OpKernel.hc_pre`/`hc_post` 每层两轮调用 `hc_attn_*`/`hc_ffn_*`；`hc_head` 单独的 Pre 风格收敛函数 L1478-1483；进网络 `unsqueeze(2).repeat(1,1,hc_mult,1)`）
- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`torchtitan_npu/converters/kernels/mhc_prepost.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/mhc_prepost.py)（@8f128cd：`MHCPreConverter`/`MHCPostConverter` 按 `get_npu_device_type()=="A5"` 选 Fused/Triton；950 `MHCPre.forward`→`torch_npu.npu_hc_pre(need_grad=True)`、`backward`→`npu_mhc_pre_sinkhorn_grad`；`MHCPost.forward`→`torch_npu.npu_hc_post`、`backward`→`npu_mhc_post_grad`；非 950 走 `MHCPreTriton`/`MHCPostTriton`，`MHCPostConverter` 在 `not use_fused_kernel` 时额外把 `HcHead` 换成 `NpuHcHead`(`MHCPreOnlyTriton`)）+ [`models/deepseek_v4/config_registry.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/deepseek_v4/config_registry.py)（`_default_converters()` 含 `npu_mhc_pre`（默认开）不含 `npu_mhc_post`；`_enable_all_converters()` 才加 `npu_mhc_post`）+ [`docs/feature_guides/npu_fused_ops.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md)（MHCPre/MHCPost converter 功能说明、950 按需开 / A3 保持关闭的性能取舍）
- 论文：[Manifold-Constrained Hyper-Connections (Xie et al., 2026)](https://arxiv.org/abs/2512.24880)
- 溯源（diff `2f82d10..2c45117` + MR）：`5df82b1` support deepseek v4（!366 merge publish into master）随 V4 0day 引入 mHC guide + `mhc.py`；`985b882` 更新 deepseek_v4_ascendc_operator_guide（!367）；`5e9e41d` Edit V4 AscendC Operator Guide（!375）；PyPTO guide 同批随 V4 发布。

## Links

- [mhc](../modules/mhc.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [pypto](../frameworks/pypto.md)（HcPre 的 PyPTO 实现）
- [ascendc](../frameworks/ascendc.md)（HcPre / HcPost 的 AscendC 实现）
- [autofuse](../frameworks/autofuse.md)（`hc_post` 经 `@torch.compile` 自动融合的并列路径，A3 实测 4x）

运行于 Atlas A3（arch_support 已覆盖 A3 / ascend-950）。
- [deepseek-v4-continue-pretrain](../../../training/guides/recipes/deepseek_v4_continue_pretrain.md)（跨域·训练：mHC 在 V4 训练侧(AutoFuse 融合小算子)）
- [mhc-train](../../../training/concepts/kernels/mhc_train.md)（跨域·训练：MindSpeed-LLM 的 mHC 训练正反向 Triton BMM + Sinkhorn 算子，与本页 AscendC 正向算子对照）