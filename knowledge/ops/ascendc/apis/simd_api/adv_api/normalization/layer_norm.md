---
type: API
title: LayerNorm
description: 对shape为[B,S,H]或[A,R]的输入数据进行LayerNorm归一化，输出归一化结果及均值、方差等，通过缩放系数γ、平移系数β和防除零系数ε加速训练收敛。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNorm

对输入数据做LayerNorm归一化，将网络层输入数据收敛以加速训练收敛。提供两种模式：对shape为[B,S,H]的输入输出归一化结果、均值和方差；对shape为[A,R]的输入输出归一化结果、均值、标准差倒数或方差。计算公式：y = γ*(x-μ)/sqrt(σ²+ε) + β，其中γ为缩放系数，β为平移系数，ε为防除零系数。模板参数T支持half/float。

提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持不同输入/输出shape模式。Tiling参数通过LayerNorm Tiling获取。模板参数isReuseSource在float时可设为true复用srcLocal内存；isBasicBlock在满足基本块要求时可提升性能。

接口参数因模式而异，通常包含：output归一化结果；outputMean/outputVariance/outputRstd输出统计量；inputX输入；gamma/beta缩放平移系数；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；H/R轴需满足32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [LayerNorm Tiling](layer_norm_tiling.md)（`related`）：Host 侧先查询临时空间并生成 LayerNormTiling，Kernel 侧 LayerNorm 直接消费该结构；H/R 对齐、isReuseSource、isBasicBlock 必须一致。
- [Normalize](normalize.md)（`related`）：当均值和方差已经由上游计算时，Normalize 可跳过 LayerNorm 的统计归约，只完成 rstd 与仿射归一化，是同一公式的可复用下游阶段。
- [WelfordFinalize](welford_finalize.md)（`related`）：WelfordFinalize 消费分块 Update 的中间态得到最终均值/方差，使大 Reduce 轴的分块统计重新接回 LayerNorm 归一化。
- [WelfordUpdate](welford_update.md)（`related`）：Reduce 轴过大时可按块调用 WelfordUpdate 累积均值和方差中间态，替代一次性 LayerNorm 统计阶段。
<!-- cannbot:related:end -->
