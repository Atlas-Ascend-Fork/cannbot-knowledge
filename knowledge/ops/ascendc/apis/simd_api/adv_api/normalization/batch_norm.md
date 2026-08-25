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

- [BatchNorm Tiling](batch_norm_tiling.md)（`same_topic`）：《BatchNorm Tiling》的任务是“获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。”。《BatchNorm》具体提供“对每一层输入做规范化处理，在batch维度上计算均值和方差进行归一化，再通过缩放和平移参数调整分布，加速训练并提升泛化能力。”，它直接用于BatchNorm Tiling 所依赖的 Welford 统计量和数据格式约束。
<!-- cannbot:related:end -->
