---
type: API
title: SetOrgInputShape
description: 设置特征矩阵Input的原始形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetOrgInputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetOrgInputShape

设置特征矩阵Input的原始形状。

函数原型：void SetOrgInputShape(int64_t orgCi, int64_t orgDi, int64_t orgHi, int64_t orgWi)

参数：
- orgCi（输入）：原始输入通道的大小。
- orgDi（输入）：原始Input D维度大小。
- orgHi（输入）：原始Input H维度大小。
- orgWi（输入）：原始Input W维度大小。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：The Conv3D tiling flow requires original input shape alongside type, weight/output shapes, padding, stride, and dilation before GetTiling.
<!-- cannbot:related:end -->
