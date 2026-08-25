---
type: API
title: SetPadding
description: void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t
  padDown, int64_t padLeft, int64_t padRight)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetPadding.md
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

- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：“SetPadding”处理void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)；“Conv3DBackpropFilterTiling”明确提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。实质衔接：SetPadding 写入反向滤波 Tiling 对象的六向 padding，随后由 GetTiling 消费；使用说明给出这一步在 Host Tiling 调用序列中的位置。
- [GetTiling](get_tiling.md)（`same_topic`）：“SetPadding”处理void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)；“GetTiling”明确获取Tiling参数。。实质衔接：SetPadding 写入反向滤波 Tiling 对象的六向 padding，随后由 GetTiling 消费；使用说明给出这一步在 Host Tiling 调用序列中的位置。
<!-- cannbot:related:end -->
