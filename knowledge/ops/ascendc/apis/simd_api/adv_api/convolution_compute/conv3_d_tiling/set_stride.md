---
type: API
title: SetStride
description: 设置Stride信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetStride

设置Stride信息。

函数原型：void SetStride(int64_t strideD, int64_t strideH, int64_t strideW)

参数：
- strideD（输入）：D方向Stride大小。
- strideH（输入）：H方向Stride大小。
- strideW（输入）：W方向Stride大小。
