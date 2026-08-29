---
type: API
title: DeepNorm
description: 在深层神经网络中替代LayerNorm，通过扩大残差连接提高Transformer稳定性，实现对shape为[B,S,H]输入数据的DeepNorm归一化。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/DeepNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DeepNorm

在深层神经网络中替代LayerNorm，通过扩大残差连接提高Transformer稳定性。计算公式：DeepNorm(x) = LayerNorm(α * X + SubLayer(X))，其中SubLayer(X)作为整体输入Tensor传入。输入shape为[B, S, H]，输出归一化结果、均值和rstd。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过DeepNorm Tiling获取。模板参数isReuseSrc在float时可设为true复用srcLocal内存（half不支持）；isBasicBlock在满足基本块要求时可设为true提升性能。

接口参数：dstLocal输出归一化结果；meanLocal/rstdLocal输出均值和标准差倒数；srcLocal输入（shape [B,S,H]）；gxLocal输入SubLayer结果；betaLocal/gammaLocal平移和缩放系数；sharedTmpBuffer临时缓存；alpha残差缩放系数；epsilon防除零系数；tiling切分信息。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DeepNorm Tiling](deep_norm_tiling.md)（`same_topic`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过DeepNorm Tiling获取。host侧Tiling接口，用于获取DeepNorm kernel计算所需的Tiling参数，分两步：通过GetDeepNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetDeepNormNDTilingInfo获取kernel侧所需tiling参数。Kernel 卡明确把 DeepNorm Tiling 作为参数来源，Host 卡给出临时空间范围和最终 tiling 结构的生成步骤；实现时必须用相同 shape、dtype 大小和复用设置生成并传入该结构。
<!-- cannbot:related:end -->
