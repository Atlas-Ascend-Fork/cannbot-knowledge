---
type: API
title: GroupNorm Tiling
description: 获取GroupNorm kernel计算时所需的Tiling参数，包括通过GetGroupNormMaxMinTmpSize获取最大最小临时空间大小和GetGroupNormNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/GroupNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GroupNorm Tiling

host侧Tiling接口，用于获取GroupNorm kernel计算所需的Tiling参数，分两步：通过GetGroupNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetGroupNormNDTilingInfo获取kernel侧所需tiling参数。

GetGroupNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetGroupNormNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(N,C,H,W)；groupNum分组数；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出GroupNormTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [GroupNorm](group_norm.md)（`related`）：“host侧Tiling接口，用于获取GroupNorm kernel计算所需的Tiling参数，分两步：通过GetGroupNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetGroupNormNDTilingInfo获取kernel侧所需tiling参数。”与“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过GroupNorm Tiling获取。模板参数isReuseSource预留（传false）。”分别给出两端正文事实；Host 侧先计算临时空间和 GroupNormTiling，Kernel 侧 GroupNorm 明确消费该 tiling，二者形成同一接口的参数生产消费链。
<!-- cannbot:related:end -->
