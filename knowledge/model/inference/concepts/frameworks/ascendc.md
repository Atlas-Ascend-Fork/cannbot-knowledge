---
type: Concept
title: AscendC
description: 'AscendC 是昇腾原生 C++ 算子编程框架，允许显式调度 Cube、Vector、Scalar 及 L0/L1/L2/UB 内存，通过 Tiling、双 Buffer 和多核流水获得较高性能上限。DeepSeek-V4 的 SAS、Compressor、LI 同时覆盖 Atlas A3 与 950PR/DT：A3 使用四阶段 SAS，950 增加 FP8 反量化阶段并以 Histograms 加速 LI 精确 Top-k；S_k=16384 时理论约 7296 cycle，对比 A3 排序路径约 28375 cycle。模板 Cost Model 以搬运不慢于计算选择基本块，值依赖分核由 AICPU 生成 metadata；具体 metadata 算子实现在外部 ops-transformer。'
tags:
- task.implementation
- topic.architecture
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a3
- '950'
---

# AscendC

## Summary

华为昇腾原生的 C++ 算子编程框架，提供对 NPU 硬件的精细控制能力，用于实现高性能融合算子。在 cann-recipes-infer 中是三种算子框架中性能上限最高的选择。

## Architecture

- 基于 C++ 模板编程，直接操作 NPU 的 Cube/Vector/Scalar 计算单元
- 提供 Tiling、双 Buffer 流水、多核调度等底层抽象
- 编译后生成可在 NPU 上直接执行的 kernel binary

## Key Features

- 精细的内存管理（L0/L1/L2/UB 显式控制）
- 多核并行调度
- 指令级流水线优化
- 支持自定义 Tiling 策略

## Usage Scenarios

- 性能关键路径上的算子实现（如 Attention、MoE dispatch）
- 需要极致性能优化的融合算子
- 现有框架无法覆盖的新算子类型

## Constraints

- 开发门槛较高，需理解 NPU 硬件架构
- 迭代速度不如 PyPTO 等高层框架

## DeepSeek-V4 框架级增强

DeepSeek-V4 0day 在 AscendC 上发布 `SparseAttnSharedKV`(SAS)、`Compressor` 两个全新融合算子，并增强 `LightningIndexer`(LI)。三算子均**同步支持 Atlas-A3 与 Ascend 950PR/DT**（实现位于 `ops/ascendc/src/`：kv_compress_epilog / indexer_compress_epilog / hc_pre / hc_post 等）。V4 带来的 AscendC 框架级能力如下（算子级细节见各 kernel 页）。

### 950PR/DT 直方图（Histograms）API 加速 Top-k

LI 的核心是在长达数十万的序列中为每 token **精确**选出分数最高的 Top-k（例 512，不能用近似）。950PR/DT 用 **Histograms 指令**：一个 cycle 把 64 个 uint8 数字分入 0-127 或 128-255 桶。方案三步：① **保序变换**（float→uint32，nan→0，负数取反，正数 ⊕2³¹）；② **多级直方图分桶**（uint32 切 4×8 位逐级 `hist` 定位第 Top-k 值的每 8 位，uint16 只需二级）；③ **向量化筛选**（按 `value_k` 比较聚集大于/等于项）。理论开销在 S_k=16384 时约 **7296 cycle**，显著优于 A3 上 sort32/mrgsort 的约 **28375 cycle**。详见 [lightning-indexer](../kernels/lightning_indexer.md)。

> Histograms 指令为 950PR/DT 平台能力，guide 以理论 cycle 推导描述其算法。

### FP8 量化模式

V4 在 950PR/DT 上为三算子适配 **FP8 量化模式**，强化昇腾芯片对低精度浮点 FP8 的类型支持。`ops/ascendc/src/kv_compress_epilog/op_host/kv_compress_epilog_tiling_arch35.h:42-43` 的 tiling 头定义 `QUANT_MDOE_GROUP_FP8 = 1` / `QUANT_MDOE_GROUP_MXFP8 = 2`（`[sic]` —— 源码符号拼写含 typo `MDOE`，语义为 GROUP_FP8 / GROUP_MXFP8），输出 dtype 支持 `DT_FLOAT8_E5M2` / `DT_FLOAT8_E4M3FN`。SAS 在 950PR/DT 为伪量化版本（KV 量化到 8bit，五阶段计算首阶段 V₀ 反量化），A3 为非量化四阶段（C₁=Q@Kᵀ / V₁=online softmax / C₂=P@V / V₂=rescale）。

### Tiling 模板编程 + 基本块 Cost Model

V4 算子的 Tiling 按平台分模板（A3 与 950PR/DT 架构不同采用不同策略），并以**基本块 Cost Model** 通过理论计算确定基本块 (baseM, baseN, baseK)：要求一轮迭代搬运耗时不超过计算耗时

$$\frac{(baseM + baseN)\times baseK \times 2\text{ Bytes}}{\text{Bandwidth}} \le \frac{baseM \times baseN \times baseK}{4096}$$

约去 baseK 得约束。例：Compressor C128A 在 A3 取 (256,128,512)、C4A 取 (128,256,512)（baseK 取 512 为昇腾亲和 Cacheline 对齐）；950PR/DT 受 L0A/L0B 容量取 256/256/256。Decode 阶段 s 轴无法分核时进一步切 d 轴（64→32）提开核数与带宽利用率。算子级 Tiling 见 [compressor](../kernels/compressor.md) / [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)。

### AICPU Scheduler 拆分（值依赖分核下沉）

SAS / LI 这类「值依赖算子」仅靠 shape 无法做好分核，需运行时实际上下文长度。V4 把 Scheduler 拆两段：**shape 可算部分**（max workspace / tiling key / block dim / tiling data）由 Host 执行；**值依赖分核**单独定义为 **AICPU（芯片内置 ARM 核）算子**，输出含分核信息的 metadata 供 NPU 算子消费 —— 既保证入图又掩盖耗时、对 aclgraph 图模式友好、每模式单次推理只算一次可复用。

> 注册命名空间为 `torch.ops.custom.npu_sparse_attn_sharedkv_metadata` / `torch.ops.custom.npu_quant_lightning_indexer_metadata`（converter/*.py register_fx_node_ge_converter）。guide 伪代码示例写 `torch_npu.npu_sparse_attn_sharedkv_metadata`（**doc≠code**，实际为 `torch.ops.custom`）。AICPU Scheduler 算子本身（`*_metadata`）的算子库在外部 `cann/ops-transformer` 仓。机制详见 [aicpu-scheduler](../techniques/aicpu_scheduler.md)。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — ops/ascendc/ 目录包含多个 AscendC 算子实现
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md)（V4 AscendC：Compressor / LI 950PR/DT 直方图 / SAS / AICPU Scheduler，MR 985b882/5e9e41d）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/ascendc/src/{kv_compress_epilog, indexer_compress_epilog, hc_pre, hc_post}`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/ops/ascendc/src) + [`torch_ops_extension/custom_ops/converter/`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/ops/ascendc/torch_ops_extension/custom_ops/converter)（FP8 dtype / metadata 算子命名空间 grep 核对）

## Known Kernels

- [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md) — Qwen3-Next Decode/MTP 阶段 GDN 融合算子（Sigmoid + L2Norm + gated delta + state update）。
- [mambav2-rmsnormgated](../kernels/mambav2_rmsnormgated.md) — Qwen3-Next GDN 输出端 RMSNorm + SiLU + Mul 融合算子，双缓冲 MTE2/V/MTE3 流水。

## Links

- [pypto](pypto.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md)
- [mambav2-rmsnormgated](../kernels/mambav2_rmsnormgated.md)
- [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)（V4 SAS AscendC 实现）
- [compressor](../kernels/compressor.md)（V4 KV 压缩融合算子 AscendC 实现：错位写入 / 基本块 Cost Model）
- [lightning-indexer](../kernels/lightning_indexer.md)（LI AscendC 实现：Tiling / TopK 指令 / Mat-Duce 量化 / ReLU 随路）
- [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md)（HcPre / HcPost 的 AscendC 实现：A3 分离架构 CV 流水、Decode 切 K / Prefill 分 token 双模板、HcPost 消除内存墙）
- [aicpu-scheduler](../techniques/aicpu_scheduler.md)（值依赖分核下沉 AICPU 的 AscendC 技术：SAS / LI 的 metadata 算子）
- [autofuse](autofuse.md)（AutoFuse Codegen 自动生成 AscendC kernel 的来路之一）
- [tilelang](tilelang.md)（TileLang AscendC 后端路径 / Developer 模式 V4 算子）
- [deepseek-v4](../models/deepseek_v4.md)（V4 0day AscendC：直方图 Top-k / FP8 模式 / AICPU Scheduler）
- [ascend-950](../platforms/ascend_950.md)（950PR/DT 直方图 API + FP8 模式 + L0A/L0B 256³ 基本块的平台来路）
- [slig](../../../training/concepts/kernels/slig.md)（跨域·训练：Ascend C 实现的 DSA 训练反向 SLIG）
- [sfag](../../../training/concepts/kernels/sfag.md)（跨域·训练：Ascend C 实现的 DSA 训练反向 SFAG）
- [sasg](../../../training/concepts/kernels/sasg.md)（跨域·训练：Ascend C 实现的 V4 SAS 反向 SASG）
- [3d-gaussian-splatting](../../../spatial/concepts/algorithms/3d_gaussian_splatting.md)（跨域·空间智能：3DGS 训推枢纽，下列自研渲染算子均以 AscendC 实现）
- [calc-render](../../../spatial/concepts/kernels/calc_render.md)（跨域·空间智能：3DGS alpha-blending 渲染前/反向算子）
- [projection-3dgs](../../../spatial/concepts/kernels/projection_3dgs.md)（跨域·空间智能：3DGS 3D→2D 投影前/反向算子）
- [spherical-harmonics](../../../spatial/concepts/kernels/spherical_harmonics.md)（跨域·空间智能：3DGS 球谐系数→颜色前/反向算子）
- [gaussian-sort](../../../spatial/concepts/kernels/gaussian_sort.md)（跨域·空间智能：3DGS tile 内高斯深度排序算子）
- [precise-intersection](../../../spatial/concepts/kernels/precise_intersection.md)（跨域·空间智能：3DGS 高斯-像素块精确相交算子）
- [gaussian-filter](../../../spatial/concepts/kernels/gaussian_filter.md)（跨域·空间智能：3DGS 视锥剔除融合算子）
- [hunyuan3d](../../../spatial/concepts/models/hunyuan3d.md)（跨域·空间智能：render_npu / 自研光栅化小算子的 AscendC 实现）
- [triton-on-ascend](../../../training/concepts/frameworks/triton_on_ascend.md)（与手写 AscendC 并列的第三条算子通道：Triton DSL 落昇腾）

<!-- cannbot:related:start -->
## 相关

- [同一算子有 AscendC / pyPTO / TileLang 多后端实现时的选型 — 当前阶段优先 AscendC](../../optimizations/experience/rules/op_backend_selection_ascendc_pypto_tilelang.md)（`related`）：默认采用 **Ascend C** 实现——维护者确认在当前阶段其性能最优，作为默认选型。；华为昇腾原生的 C++ 算子编程框架，提供对 NPU 硬件的精细控制能力，用于实现高性能融合算子。。前者给出 cann-recipes-infer 多后端并存时优先 Ascend C 的当前选型，后者说明 AscendC 以 C++ 模板和硬件精细控制实现高性能融合算子的能力基础，形成后端选择到框架能力的下钻链。
- [自定义算子接图模式的 lowering 正确性：converter 按 GE IR 原型对齐 + meta 函数显式声明输出 dtype](../../runbooks/precision/custom_op_graph_lowering_converter_meta_correctness.md)（`related`）：带自定义 ［AscendC］(../../concepts/frameworks/ascendc.md) 算子的模型在 **eager 下正常、一入图（ge_graph / torch 图捕获）就报错或结果错**。；华为昇腾原生的 C++ 算子编程框架，提供对 NPU 硬件的精细控制能力，用于实现高性能融合算子。。AscendC 概念页定义真实 NPU kernel 的实现框架，运行手册说明这类 kernel 接图模式时还必须让 meta 输出与 GE converter 原型精确对齐。
<!-- cannbot:related:end -->
