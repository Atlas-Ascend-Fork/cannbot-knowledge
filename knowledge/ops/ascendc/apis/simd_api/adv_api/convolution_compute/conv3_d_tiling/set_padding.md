---
type: API
title: SetPadding
description: void SetPadding(int64_t padHead, int64_t padTail, int64_t padUp, int64_t
  padDown, int64_t padLeft, int64_t padRight)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetPadding.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetPadding

设置Pad信息。

函数原型：void SetPadding(int64_t padHead, int64_t padTail, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)

参数：
- padHead（输入）：D方向前Padding大小。
- padTail（输入）：D方向后Padding大小。
- padUp（输入）：H方向上Padding大小。
- padDown（输入）：H方向下Padding大小。
- padLeft（输入）：W方向左Padding大小。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：接口卡的“设置Pad信息。”说明 SetPadding 的单一职责；使用说明要求“如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。”，把它放入 GetTiling 前的参数组装顺序。
<!-- cannbot:related:end -->
