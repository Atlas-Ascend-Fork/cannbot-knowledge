---
type: API
title: Conv3DUsage
description: Ascend C提供Conv3D高阶API，用于快速实现3维卷积正向矩阵运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3D_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DUsage

Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。3维正向卷积的示意图如图1，其计算公式为： - X为Conv3D卷积的特征矩阵Input。 - W为Conv3D卷积的权重矩阵Weight。 - B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。 图1 3维正向卷积示意图
