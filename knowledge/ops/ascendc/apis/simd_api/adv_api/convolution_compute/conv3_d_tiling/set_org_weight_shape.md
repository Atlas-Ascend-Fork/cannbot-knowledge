---
type: API
title: SetOrgWeightShape
description: 设置权重矩阵Weight的原始形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetOrgWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetOrgWeightShape

设置权重矩阵Weight的原始形状。

函数原型：void SetOrgWeightShape(int64_t orgCo, int64_t orgKd, int64_t orgKh, int64_t orgKw)

参数：
- orgCo（输入）：原始输出通道的大小。
- orgKd（输入）：原始Weight D维度大小。
- orgKh（输入）：原始Weight H维度大小。
- orgKw（输入）：原始Weight W维度大小。
