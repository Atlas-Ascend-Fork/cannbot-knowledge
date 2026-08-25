---
type: API
title: GroupNorm
description: 对shape为[N,C,H,W]的输入，将每个[C,H,W]在C维度上分为groupNum组并对每一组进行标准化，再通过可训练的缩放参数γ和平移参数β进行调整。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/GroupNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GroupNorm

对shape为[N, C, H, W]的输入，将每个[C, H, W]在C维度上分为groupNum组，对每一组进行标准化（计算均值和标准差），最后对标准化结果进行缩放（γ）和平移（β）。输出归一化结果、均值和方差。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过GroupNorm Tiling获取。模板参数isReuseSource预留（传false）。

接口参数：output输出归一化结果；outputMean/outputVariance输出均值和方差；inputX输入；gamma/beta输入缩放和平移系数；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。
