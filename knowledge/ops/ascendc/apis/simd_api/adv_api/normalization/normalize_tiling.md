---
type: API
title: Normalize Tiling
description: 获取Normalize kernel计算时所需的Tiling参数，通过GetNormalizeMaxMinTmpSize获取接口计算所需最大和最小临时空间大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/Normalize-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Normalize Tiling

host侧Tiling接口，用于获取Normalize kernel计算所需的Tiling参数，分两步：通过GetNormalizeMaxMinTmpSize获取最大和最小临时空间大小；通过GetNormalizeNDTilingInfo获取kernel侧所需tiling参数。

GetNormalizeMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetNormalizeNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(A,R)；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出NormalizeTiling结构体。
