---
type: Concept
title: AscendC
description: AscendC 是昇腾原生 C++ 算子编程框架，提供 Cube、Vector、Scalar 调度、Tiling 和片上缓冲区管理；L2 缓存配置受接口、产品和版本限制。以 DeepSeek-V4 的 SAS、Compressor、LightningIndexer 说明 A3 与 950PR/DT 的实现差异，性能估算方法、对照口径与实测边界见正文。
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
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetL2CacheHint.md
  role: constraint
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/clock_and_timestamp.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-28T06:00:57Z'
platforms:
- a3
- '950'
---
# AscendC

## Summary

华为昇腾原生的 C++ 算子编程框架，提供对 NPU 硬件的精细控制能力，用于实现高性能融合算子。具体后端选择需结合算子实现、图模式和目标平台验证，不能由框架名称判断性能排名。

## Architecture

- 基于 C++ 模板编程，直接操作 NPU 的 Cube/Vector/Scalar 计算单元
- 提供 Tiling、双 Buffer 流水、多核调度等底层抽象
- 编译后生成可在 NPU 上直接执行的 kernel binary

## Key Features

- 按目标平台管理 L0/L1/UB 等片上缓冲区，组织数据搬运与复用；L2 缓存策略需单独核对接口支持范围
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
- L2 缓存策略有平台和模式限制。[SetL2CacheHint](../../../../ops/ascendc/apis/simd_api/basic_api/data_structures/global_tensor/set_l2_cache_hint.md) 设置 GlobalTensor 是否启用 L2 Cache；固定版本文档列出 A2、A3、950PR/DT 支持，而 Atlas 200I/500 A2 推理产品不支持，并明确 `CACHE_MODE_PERSISTENT` 驻留模式尚不支持。不能把这一能力概括为全平台的 L2 显式分配或驻留保证；使用时还需核对目标 CANN 版本。

## DeepSeek-V4 框架级增强

DeepSeek-V4 0day 在 AscendC 上发布 `SparseAttnSharedKV`(SAS)、`Compressor` 两个全新融合算子，并增强 `LightningIndexer`(LI)。三算子均**同步支持 Atlas-A3 与 Ascend 950PR/DT**（实现位于 `ops/ascendc/src/`：kv_compress_epilog / indexer_compress_epilog / hc_pre / hc_post 等）。V4 带来的 AscendC 框架级能力如下（算子级细节见各 kernel 页）。

### 950PR/DT 直方图（Histograms）API 加速 Top-k

LI 的核心是在长达数十万的序列中为每 token **精确**选出分数最高的 Top-k（例 512，不能用近似）。950PR/DT 用 **Histograms 指令**：一个 cycle 把 64 个 uint8 数字分入 0-127 或 128-255 桶。方案三步：① **保序变换**（float→uint32，nan→0，负数取反，正数 ⊕2³¹）；② **多级直方图分桶**（uint32 切 4×8 位逐级 `hist` 定位第 Top-k 值的每 8 位，uint16 只需二级）；③ **向量化筛选**（按 `value_k` 比较聚集大于/等于项）。具体算法见 [lightning-indexer](../kernels/lightning_indexer.md)，以下说明性能数字的获取方法和比较范围。

#### 理论周期如何得到、可以比较什么

数字来自 [固定版本 Guide 的「实现指令和理论开销」](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md#top-k-950prdt-方案)。估算对象为一个 Query 的 Top-k 阶段，Score 保序变换为 uint32，`S_k=16384`、`k=512`；不含 LI 的矩阵乘法、整网调度等其他阶段。

| 方案与平台 | 从来源取得估算值的方法 | 该例理论周期 |
| --- | --- | --- |
| 950PR/DT：直方图与向量化筛选 | 累加四级 hist/find 与 findGTO/findEQ 共十段的指令开销，得到 `111 × (S_k / 256) + 192` | `111 × 64 + 192 = 7296` cycle |
| A3：sort32 与 mrgsort | 按同一 Guide 给出的排序/归并估算式计算，见下式 | 约 `28375` cycle |

$$C_{A3} = \frac{1.36S_k + 3.32k + \left\lceil \frac{\max(\log_2(k)-5,0)}{2}S_k \right\rceil}{2}$$

代入同一组 `S_k`、`k`，A3 估算值为 `28375.04` cycle，两者的理论周期比约为 `3.89`。这是两个平台各自指令模型的对照，不能视为同平台替换算法后的实测加速比，也不能直接换算成整算子时延、TTFT 或 TPOT 收益。该 Guide 未给出这组数字对应的真机 Trace 或重复测量统计，本卡没有补造实测结果。

#### 如何补充实测与实现对照

1. 固定平台、CANN/编译版本、输入 Score 类型和分布、`S_k`、`k` 及 Query 数；先验证精确 Top-k 的结果正确，再比较性能。同平台有可运行的等价实现时作为基线，缺少对照时只报告观测值，不声称实现收益。
2. 若测 Top-k 局部周期，在同一线程的被测段前后使用 `clock()` 取差值；把打印移出测量区，区分预热与稳态，记录重复次数和分布，并说明同步等待、编译优化和调度影响。测量范围需与理论模型对齐；完整测量边界见 [Kernel 周期与时间戳测量](../../../../contrib/ascendc/runbooks/performance/kernel_clock_and_time_stamp_measurement.md)。
3. 同时记录基线周期、候选周期与理论估算，分别报告实测相对理论的偏差和 `1 - 候选周期 / 基线周期` 的周期下降比例。局部周期结果只支持局部结论；整算子耗时与整网指标应单独测量，不能沿用该比例。本段是复测方法，本次未执行设备测量。

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
- [SetL2CacheHint 固定版本文档](https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetL2CacheHint.md) — 产品支持情况与驻留模式边界；接口可用不代表所有缓存模式均可用。
- [clock 与时间戳固定版本说明](https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/clock_and_timestamp.md) — 同线程局部周期差、打印位置及测量干扰；不将局部周期冒充完整算子或整网耗时。

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
