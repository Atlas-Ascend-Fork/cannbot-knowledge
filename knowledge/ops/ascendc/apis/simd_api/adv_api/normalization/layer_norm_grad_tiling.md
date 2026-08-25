---
type: API
title: LayerNormGrad Tiling
description: 获取LayerNormGrad kernel计算时所需的Tiling参数，包括通过GetLayerNormGradMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormGradNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNormGrad-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNormGrad Tiling

host侧Tiling接口，用于获取LayerNormGrad kernel计算所需的Tiling参数，分两步：通过GetLayerNormGradMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormGradNDTilingInfo获取kernel侧所需tiling参数。

GetLayerNormGradMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetLayerNormGradNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(B,S,H)；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出LayerNormGradTiling结构体。
