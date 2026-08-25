---
type: API
title: TopKTiling
description: 获取TopK kernel计算时所需的Tiling参数，包括临时空间大小和tiling信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/TopK-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TopK Tiling

host侧Tiling接口，用于获取TopK kernel计算所需的Tiling参数，分两步：通过GetTopKMaxMinTmpSize获取最大和最小临时空间大小；通过GetTopKNDTilingInfo获取kernel侧所需tiling参数。

GetTopKMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetTopKNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出TopKParams结构体。约束：需保证内轴满足32B对齐。
