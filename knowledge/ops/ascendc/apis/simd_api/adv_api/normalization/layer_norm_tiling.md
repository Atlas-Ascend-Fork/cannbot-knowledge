---
type: API
title: LayerNorm Tiling
description: 获取LayerNorm kernel计算时所需的Tiling参数，包括通过GetLayerNormMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNorm Tiling

host侧Tiling接口，用于获取LayerNorm kernel计算所需的Tiling参数，分两步：通过GetLayerNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormNDTilingInfo（或GetLayerNormTmpBufferFactorSize）获取kernel侧所需tiling参数。

GetLayerNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource是否复用源操作数；isOutputRstd输出是否含rstd；maxValue/minValue输出临时空间范围。

GetLayerNormNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(B,S,H)或(A,R)；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出LayerNormTiling结构体。约束：需保证各维度大于0且H/R满足32B对齐。
