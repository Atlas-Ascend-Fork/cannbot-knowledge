---
type: API
title: BatchNorm
description: 对每一层输入做规范化处理，在batch维度上计算均值和方差进行归一化，再通过缩放和平移参数调整分布，加速训练并提升泛化能力。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/BatchNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# BatchNorm

对每一层输入做规范化处理，在batch维度上计算均值和方差，对输入特征进行归一化后进行缩放和平移，加速训练并提高泛化能力。输入shape为[B, S, H]，输出归一化结果、均值（shape [S,H]）和方差（shape [S,H]）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过BatchNorm Tiling获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求（originB为8的倍数，S*H为64的倍数且小于2048）时可设为true提升性能。

接口参数：output输出归一化结果；outputMean/outputVariance输出均值和方差；inputX输入（shape [B,S,H]，S*H需32B对齐，支持与output地址重叠）；gamm/beta输入缩放和平移系数（shape [B]，32B对齐）；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；S*H需32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [BatchNorm Tiling](batch_norm_tiling.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过BatchNorm Tiling获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求（originB为8的倍数，S*H为64的倍数且小于2048）时可设为true提升性能。；host侧Tiling接口，用于获取BatchNorm kernel计算所需的Tiling参数，分两步：通过GetBatchNormMaxMinTmpSize获取最大和最小临时空间大小（minValue保证功能正确，maxValue提升性能）；通过GetBatchNormNDTilingInfo获取kernel侧所需tiling参数（含切分信息、临时空间位置等），开发者无需关注tiling结构体细节，直接传入BatchNorm高阶API使用。；BatchNorm 明确消费 BatchNorm Tiling 生成的临时空间范围和切分参数，Tiling 页又规定如何产生这些参数，二者构成 Host 规划到 Kernel 调用的直接接口链。
<!-- cannbot:related:end -->
