---
type: API
title: SetInputShape
description: 设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetInputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputShape

设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。

函数原型：void SetInputShape(int64_t n, int64_t c, int64_t d, int64_t h, int64_t w)

参数：
- n：输入输入Input的Batch值。
- c：输入输入Input的Channel值。
- d：输入输入Input的Depth值。
- h：输入输入Input的Height值。
- w：输入输入Input的Width值。
