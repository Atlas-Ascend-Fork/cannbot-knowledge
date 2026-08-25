---
type: API
title: SetGradOutputShape
description: 设置GradOutput的形状：Batch、Channel、Depth、Height、Width。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetGradOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGradOutputShape

设置GradOutput的形状：Batch、Channel、Depth、Height、Width。

函数原型：void SetGradOutputShape(int64_t n, int64_t c, int64_t d, int64_t h, int64_t w)

参数：
- n：输入输入GradOutput的Batch值。
- c：输入输入GradOutput的Channel值。
- d：输入输入GradOutput的Depth值。
- h：输入输入GradOutput的Height值。
- w：输入输入GradOutput的Width值。
