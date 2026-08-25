---
type: API
title: SetPadding
description: void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t
  padDown, int64_t padLeft, int64_t padRight)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetPadding.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetPadding

设置Pad信息。

函数原型：void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)

参数：
- padFront（输入）：卷积正向过程中Input Depth维度的前方向Padding大小。
- padBack（输入）：卷积正向过程中Input Depth维度的后方向Padding大小。
- padUp（输入）：卷积正向过程中Input Height维度的上方向Padding大小。
- padDown（输入）：卷积正向过程中Input Height维度的下方向Padding大小。
- padLeft（输入）：卷积正向过程中Input Width维度的左方向Padding大小。

<!-- cannbot:related:start -->
## 相关

- [SetOutputPadding](set_output_padding.md)（`related`）：SetOutputPadding 与《SetPadding》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetStride](set_stride.md)（`related`）：步长改变反卷积输出尺寸推导，需与前后/上下/左右 padding 一起满足 shape 公式。
<!-- cannbot:related:end -->
