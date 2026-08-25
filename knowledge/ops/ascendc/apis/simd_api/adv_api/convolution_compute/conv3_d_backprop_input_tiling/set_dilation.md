---
type: API
title: SetDilation
description: 设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetDilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetDilation

设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。

函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)

参数：
- dilationD（输入）：卷积核Weight的Depth方向扩张大小。
- dilationH（输入）：卷积核Weight的Height方向扩张大小。
- dilationW（输入）：卷积核Weight的Width方向扩张大小。
