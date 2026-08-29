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

- [LayerNormGradBeta Tiling](layer_norm_grad_beta_tiling.md)（`related`）：“host侧Tiling接口，用于获取LayerNormGradBeta kernel计算所需的Tiling参数，分两步：通过GetLayerNormGradBetaMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormGradBetaNDTilingInfo获取kernel侧所需tiling参数。”；“获取LayerNorm反向传播的gamma和beta梯度，与LayerNormGrad配合使用。接收LayerNormGrad输出的resForGamma和上游梯度inputDy，计算并输出pd_gamma和pd_beta。”。Host 两步 tiling产出 LayerNormGradBeta kernel 所需临时空间和切分结构，kernel 再消费 resForGamma 与 inputDy 计算梯度。
- [LayerNormGrad](layer_norm_grad.md)（`same_topic`）：计算LayerNorm的反向传播梯度。可单独使用输出pd_x和resForGamma；也可与LayerNormGradBeta配合使用，将resForGamma传递给LayerNormGradBeta同时得到pd_x、pd_gamma和pd_beta。输入shape为［B,S,H］。模板参数T支持half/float。；获取LayerNorm反向传播的gamma和beta梯度，与LayerNormGrad配合使用。接收LayerNormGrad输出的resForGamma和上游梯度inputDy，计算并输出pd_gamma和pd_beta。模板参数T支持half/float。。前一接口产生 resForGamma，后一接口把它作为必需输入继续计算 gamma 与 beta 梯度，明确构成 LayerNorm 反向的生产者到消费者调用链。
<!-- cannbot:related:end -->
