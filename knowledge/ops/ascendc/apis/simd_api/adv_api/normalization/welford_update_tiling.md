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
