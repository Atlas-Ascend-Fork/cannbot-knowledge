---
type: API
title: SetSingleOutputShape
description: 设置单核上结果矩阵Output的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetSingleOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleOutputShape

设置单核上结果矩阵Output的形状。

函数原型：void SetSingleOutputShape(int64_t singleCo, int64_t singleDo, int64_t singleM)

参数：
- singleCo（输入）：单核上输出通道的大小。
- singleDo（输入）：单核上Output D维度大小。
- singleM（输入）：单核上Output M维度大小。
