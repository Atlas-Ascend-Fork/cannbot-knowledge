---
type: API
title: LayerNormGradBeta
description: 'LayerNormGradBeta接口用于获取反向beta/gamma的数值，和LayerNormGrad共同输出pdx, gamma和beta：
  算法公式为: ! !'
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNormGradBeta.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNormGradBeta

获取LayerNorm反向传播的gamma和beta梯度，与LayerNormGrad配合使用。接收LayerNormGrad输出的resForGamma和上游梯度inputDy，计算并输出pd_gamma和pd_beta。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过LayerNormGradBeta Tiling获取。模板参数isReuseSource预留（传false）。

接口参数：outputPdGamma输出gamma的梯度；outputPdBeta输出beta的梯度；resForGamma输入LayerNormGrad的中间结果；inputDy输入上游梯度；sharedTmpBuffer临时缓存；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [LayerNormGrad Tiling](layer_norm_grad_tiling.md)（`related`）：《LayerNormGrad Tiling》处理“获取LayerNormGrad kernel计算时所需的Tiling参数，包括通过GetLayerNormGradMaxMinTmpSize获取最大最小临时空间大小和GetLayerNormGradNDTilingInfo获取tiling参数。”。《LayerNormGradBeta》明确“LayerNormGradBeta接口用于获取反向beta/gamma的数值，和LayerNormGrad共同输出pdx, gamma和beta： 算法公式为:”，可直接用于核对LayerNormGrad 主输出与 Beta/Gamma 梯度的配套 Tiling 合同。
- [LayerNormGrad](layer_norm_grad.md)（`same_topic`）：《LayerNormGrad》处理“LayerNormGrad是一个函数，用于计算LayerNorm的反向传播梯度。该接口单独使用会输出x、resForGamma；也可以和LayerNormGradBeta配合使用，输出的resForGamma传递给LayerNormGradBeta， LayerNormGradBeta接口会输出gamma和beta，配合使用时就可以同时得到x、Gamma、beta。 算法公式为:”。《LayerNormGradBeta》提供“LayerNormGradBeta接口用于获取反向beta/gamma的数值，和LayerNormGrad共同输出pdx, gamma和beta： 算法公式为:”，其具体合同或探针直接接入LayerNormGrad 与 Beta/Gamma 后段及两侧 Tiling 的输出传递合同。
- [LayerNormGradBeta Tiling](layer_norm_grad_beta_tiling.md)（`same_topic`）：LayerNormGradBetaTiling 计算的临时空间与切分参数专供 LayerNormGradBeta kernel 使用，是同一接口的 Host/Kernel 两端。
<!-- cannbot:related:end -->
