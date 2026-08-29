---
type: API
title: LayerNormGrad
description: 'LayerNormGrad是一个函数，用于计算LayerNorm的反向传播梯度。该接口单独使用会输出x、resForGamma；也可以和LayerNormGradBeta配合使用，输出的resForGamma传递给LayerNormGradBeta，
  LayerNormGradBeta接口会输出gamma和beta，配合使用时就可以同时得到x、Gamma、beta。 算法公式为:'
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/LayerNormGrad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LayerNormGrad

计算LayerNorm的反向传播梯度。可单独使用输出pd_x和resForGamma；也可与LayerNormGradBeta配合使用，将resForGamma传递给LayerNormGradBeta同时得到pd_x、pd_gamma和pd_beta。输入shape为[B,S,H]。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过LayerNormGrad Tiling获取。模板参数isReuseSource预留（传false）。

接口参数：outputPdX输出x的梯度；outputResForGamma输出给LayerNormGradBeta的中间结果；inputDy输入上游梯度；inputX/inputMean/inputVariance输入前向数据；inputGamma输入缩放系数；sharedTmpBuffer临时缓存；tiling切分信息。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [LayerNormGrad Tiling](layer_norm_grad_tiling.md)（`same_topic`）：“host侧Tiling接口，用于获取LayerNormGrad kernel计算所需的Tiling参数，分两步：通过GetLayerNormGradMaxMinTmpSize获取最大和最小临时空间大小；通过GetLayerNormGradNDTilingInfo获取kernel侧所需tiling参数。”与“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过LayerNormGrad Tiling获取。模板参数isReuseSource预留（传false）。”分别给出双端正文事实；Kernel 卡明确消费 LayerNormGrad Tiling 的结果，Tiling 卡给出临时空间和 LayerNormGradTiling 生成步骤，二者定义同一反向归一化接口的 Host/Device 交接。
- [LayerNormGradBeta](layer_norm_grad_beta.md)（`same_topic`）：计算LayerNorm的反向传播梯度。可单独使用输出pd_x和resForGamma；也可与LayerNormGradBeta配合使用，将resForGamma传递给LayerNormGradBeta同时得到pd_x、pd_gamma和pd_beta。输入shape为［B,S,H］。模板参数T支持half/float。；获取LayerNorm反向传播的gamma和beta梯度，与LayerNormGrad配合使用。接收LayerNormGrad输出的resForGamma和上游梯度inputDy，计算并输出pd_gamma和pd_beta。模板参数T支持half/float。。前一接口产生 resForGamma，后一接口把它作为必需输入继续计算 gamma 与 beta 梯度，明确构成 LayerNorm 反向的生产者到消费者调用链。
<!-- cannbot:related:end -->
