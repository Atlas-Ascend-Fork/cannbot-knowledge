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

<!-- cannbot:related:start -->
## 相关

- [LayerNormGradBeta](layer_norm_grad_beta.md)（`related`）：《LayerNormGrad Tiling》处理“获取LayerNormGrad kernel计算时所需的Tiling参数，包括通过GetLayerNormGradMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormGradNDTilingInfo获取tiling参数。”。《LayerNormGradBeta》明确“LayerNormGradBeta接口用于获取反向beta/gamma的数值，和LayerNormGrad共同输出pdx, gamma和beta： 算法公式为:”，可直接用于核对LayerNormGrad 主输出与 Beta/Gamma 梯度的配套 Tiling 合同。
- [LayerNormGradBeta Tiling](layer_norm_grad_beta_tiling.md)（`related`）：联合使用时 LayerNormGrad 与 LayerNormGradBeta 各有 Host Tiling，前者产出的中间张量形状和切分需要与后者的 beta/gamma 归约阶段衔接。
- [LayerNormGrad](layer_norm_grad.md)（`same_topic`）：《LayerNormGrad》处理“LayerNormGrad是一个函数，用于计算LayerNorm的反向传播梯度。该接口单独使用会输出x、resForGamma；也可以和LayerNormGradBeta配合使用，输出的resForGamma传递给LayerNormGradBeta， LayerNormGradBeta接口会输出gamma和beta，配合使用时就可以同时得到x、Gamma、beta。 算法公式为:”。《LayerNormGrad Tiling》提供“获取LayerNormGrad kernel计算时所需的Tiling参数，包括通过GetLayerNormGradMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormGradNDTilingInfo获取tiling参数。”，其具体合同或探针直接接入LayerNormGrad 与 Beta/Gamma 后段及两侧 Tiling 的输出传递合同。
<!-- cannbot:related:end -->
