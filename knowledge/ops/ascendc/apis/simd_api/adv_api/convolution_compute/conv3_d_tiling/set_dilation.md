---
type: API
title: SetDilation
description: 设置Dilation信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetDilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetDilation

设置Dilation信息。

函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)

参数：
- dilationD（输入）：D方向Dilation大小。
- dilationH（输入）：H方向Dilation大小。
- dilationW（输入）：W方向Dilation大小。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：接口卡给出“函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)”；使用说明要求“如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。”，把三个 dilation 维度参数放入 Conv3D Tiling 的调用顺序。
<!-- cannbot:related:end -->
