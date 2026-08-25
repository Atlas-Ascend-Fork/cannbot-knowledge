---
type: API
title: WelfordUpdate
description: Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/WelfordUpdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# WelfordUpdate

Welford算法的前处理接口，用于在线逐步计算均值和方差的中间结果。与WelfordFinalize配合使用，通过切分Reduce轴实现等效LayerNorm计算。分n次调用本接口，每次处理切分后的一块数据[1,k]，逐步累加计算前i块数据的均值和方差中间结果。第一次调用时Meant_0和M_0需为全0数据。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过WelfordUpdate Tiling获取。

接口参数：outputMean输出当前累加均值；outputM输出当前方差中间结果；inputX输入当前块数据；inputMean/inputM输入上一次的累加结果（第一次为全0）；sharedTmpBuffer临时缓存；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [BatchNorm Tiling](batch_norm_tiling.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordUpdate》具体提供“Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [GroupNorm](group_norm.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordUpdate》明确提供“Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [LayerNorm](layer_norm.md)（`related`）：Reduce 轴过大时可按块调用 WelfordUpdate 累积均值和方差中间态，替代一次性 LayerNorm 统计阶段。
- [WelfordFinalize Tiling](welford_finalize_tiling.md)（`related`）：WelfordFinalize 消费 WelfordUpdate 产生的在线均值/方差中间量，两者联合完成大 Reduce 轴的 LayerNorm 等效计算。
- [Normalize](normalize.md)（`same_topic`）：Normalize 与《WelfordUpdate》的实质衔接是：Normalize 依赖 tiling、归约统计和 Rsqrt，所选卡片覆盖 padding、NaN/rstd 与同步故障。
- [WelfordFinalize](welford_finalize.md)（`same_topic`）：WelfordUpdate 与《WelfordFinalize》的实质衔接是：WelfordUpdate tiling 生成 Update 参数，Update 的统计量再由 Finalize 及其 tiling 完成归一化输出。
- [WelfordUpdate Tiling](welford_update_tiling.md)（`same_topic`）：WelfordUpdate 与《WelfordUpdate Tiling》的实质衔接是：WelfordUpdate tiling 生成 Update 参数，Update 的统计量再由 Finalize 及其 tiling 完成归一化输出。
<!-- cannbot:related:end -->
