---
type: API
title: DeepNorm Tiling
description: 获取DeepNorm kernel计算时所需的Tiling参数，包括通过GetDeepNormMaxMinTmpSize获取最大最小临时空间大小和GetDeepNormTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/DeepNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DeepNorm Tiling

host侧Tiling接口，用于获取DeepNorm kernel计算所需的Tiling参数，分两步：通过GetDeepNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetDeepNormNDTilingInfo获取kernel侧所需tiling参数。

GetDeepNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSrc是否复用源操作数；maxValue/minValue输出临时空间范围。

GetDeepNormNDTilingInfo参数：ascendcPlatform平台信息；srcShape(B,S,H)输入shape；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出DeepNormTiling结构体。约束：需保证B、S、H均大于0且H满足32B对齐。

<!-- cannbot:related:start -->
## 相关

- [DeepNorm](deep_norm.md)（`same_topic`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过DeepNorm Tiling获取。host侧Tiling接口，用于获取DeepNorm kernel计算所需的Tiling参数，分两步：通过GetDeepNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetDeepNormNDTilingInfo获取kernel侧所需tiling参数。Kernel 卡明确把 DeepNorm Tiling 作为参数来源，Host 卡给出临时空间范围和最终 tiling 结构的生成步骤；实现时必须用相同 shape、dtype 大小和复用设置生成并传入该结构。
<!-- cannbot:related:end -->
