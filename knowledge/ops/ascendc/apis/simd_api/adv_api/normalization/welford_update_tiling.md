---
type: API
title: WelfordUpdate Tiling
description: 获取WelfordUpdate kernel计算时所需的Tiling参数，通过GetWelfordUpdateMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/WelfordUpdate-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# WelfordUpdate Tiling

host侧Tiling接口，用于获取WelfordUpdate kernel计算所需的Tiling参数，分两步：通过GetWelfordUpdateMaxMinTmpSize获取最大和最小临时空间大小；通过GetWelfordUpdateNDTilingInfo获取kernel侧所需tiling参数。

GetWelfordUpdateMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetWelfordUpdateNDTilingInfo参数：ascendcPlatform平台信息；输入shape信息；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出WelfordUpdateTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [BatchNorm Tiling](batch_norm_tiling.md)（`related`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《WelfordUpdate Tiling》具体提供“获取WelfordUpdate kernel计算时所需的Tiling参数，通过GetWelfordUpdateMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
- [GroupNorm](group_norm.md)（`related`）：《GroupNorm》处理“对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。”。《WelfordUpdate Tiling》明确提供“获取WelfordUpdate kernel计算时所需的Tiling参数，通过GetWelfordUpdateMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。”，其参数、调用或验证步骤直接接入GroupNorm 的分组统计、Welford 计算、Tiling 与格式约束。
- [WelfordFinalize Tiling](welford_finalize_tiling.md)（`related`）：Update 与 Finalize 的 Tiling 分别配置在线统计的局部更新和最终合并，需保持切分/counts 一致。
- [WelfordUpdate](welford_update.md)（`same_topic`）：WelfordUpdate 与《WelfordUpdate Tiling》的实质衔接是：WelfordUpdate tiling 生成 Update 参数，Update 的统计量再由 Finalize 及其 tiling 完成归一化输出。
<!-- cannbot:related:end -->
