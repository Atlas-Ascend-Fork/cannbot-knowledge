---
type: API
title: WelfordFinalize
description: Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/WelfordFinalize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# WelfordFinalize

Welford算法的后处理接口，用于在线计算均值和方差的最终结果。与WelfordUpdate配合使用，通过切分Reduce轴实现等效LayerNorm计算。Welford方法无需存储所有样本即可逐步计算均值和方差，适合处理海量数据且只需一次遍历。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过WelfordFinalize Tiling获取。接口接收WelfordUpdate输出的均值和方差中间结果，计算最终的均值和方差。支持带尾块（带counts参数）和不带尾块两种场景，方差计算支持系数修正和非修正模式。

接口参数：outputMean输出最终均值；outputVariance输出最终方差；inputMean/inputVariance输入WelfordUpdate的中间结果；sharedTmpBuffer临时缓存；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [BatchNorm Tiling](batch_norm_tiling.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordFinalize》具体提供“Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [GroupNorm](group_norm.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordFinalize》明确提供“Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [LayerNorm](layer_norm.md)（`related`）：WelfordFinalize 消费分块 Update 的中间态得到最终均值/方差，使大 Reduce 轴的分块统计重新接回 LayerNorm 归一化。
- [WelfordFinalize Tiling](welford_finalize_tiling.md)（`related`）：WelfordFinalize Tiling 生成该 kernel 的临时空间与 WelfordFinalizeTiling 参数；kernel 正文是这些参数的直接消费者。
- [Normalize](normalize.md)（`same_topic`）：Normalize 与《WelfordFinalize》的实质衔接是：Normalize 依赖 tiling、归约统计和 Rsqrt，所选卡片覆盖 padding、NaN/rstd 与同步故障。
- [WelfordUpdate](welford_update.md)（`same_topic`）：WelfordUpdate 与《WelfordFinalize》的实质衔接是：WelfordUpdate tiling 生成 Update 参数，Update 的统计量再由 Finalize 及其 tiling 完成归一化输出。
<!-- cannbot:related:end -->
