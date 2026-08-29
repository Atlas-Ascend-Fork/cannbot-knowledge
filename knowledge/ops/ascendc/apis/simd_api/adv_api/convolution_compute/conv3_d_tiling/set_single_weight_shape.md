---
type: API
title: SetSingleWeightShape
description: 设置单核上权重矩阵Weight的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetSingleWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleWeightShape

设置单核上权重矩阵Weight的形状。

函数原型：void SetSingleWeightShape(int64_t singleCi, int64_t singleKd, int64_t singleKh, int64_t singleKw)

参数：
- singleCi（输入）：单核上输入通道的大小。
- singleKd（输入）：单核上Weight D维度大小。
- singleKh（输入）：单核上Weight H维度大小。
- singleKw（输入）：单核上Weight W维度大小。
