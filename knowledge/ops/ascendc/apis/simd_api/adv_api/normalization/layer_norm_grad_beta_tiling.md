---
type: API
title: LayerNormGradBeta Tiling
description: 获取LayerNormGradBeta kernel计算时所需的Tiling参数，包括通过GetLayerNormGradBetaMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormGradBetaNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNormGradBeta-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNormGradBeta Tiling

host侧Tiling接口，用于获取LayerNormGradBeta kernel计算所需的Tiling参数，分两步：通过GetLayerNormGradBetaMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormGradBetaNDTilingInfo获取kernel侧所需tiling参数。

GetLayerNormGradBetaMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetLayerNormGradBetaNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(B,S,H)；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出LayerNormGradBetaTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [LayerNormGrad](layer_norm_grad.md)（`related`）：LayerNormGrad 先产出 pdx 与 resForGamma，LayerNormGradBeta 再消费 resForGamma 得到 gamma/beta；Tiling 必须围绕这条两阶段数据契约安排。
- [LayerNormGrad Tiling](layer_norm_grad_tiling.md)（`related`）：联合使用时 LayerNormGrad 与 LayerNormGradBeta 各有 Host Tiling，前者产出的中间张量形状和切分需要与后者的 beta/gamma 归约阶段衔接。
- [LayerNormGradBeta](layer_norm_grad_beta.md)（`same_topic`）：LayerNormGradBetaTiling 计算的临时空间与切分参数专供 LayerNormGradBeta kernel 使用，是同一接口的 Host/Kernel 两端。
<!-- cannbot:related:end -->
