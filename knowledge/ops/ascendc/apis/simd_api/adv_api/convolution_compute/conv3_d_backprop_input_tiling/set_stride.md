---
type: API
title: SetStride
description: 设置Stride信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetStride

设置Stride信息。

函数原型：void SetStride(int64_t strideD, int64_t strideH, int64_t strideW)

参数：
- strideD（输入）：卷积正向过程中Depth方向Stride的大小。
- strideH（输入）：卷积正向过程中Height方向Stride的大小。
- strideW（输入）：卷积正向过程中Width方向Stride的大小。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetStride 等几何配置最终由 GetTiling 固化为 Kernel 参数。
- [SetDilation](set_dilation.md)（`related`）：Stride 与 Dilation 共同决定 GradOutput 到 Input 的采样几何，Host 侧必须以同一 D/H/W 轴序配置。
- [SetGradOutputShape](set_grad_output_shape.md)（`related`）：GradOutput shape 与 stride 共同决定反推 Input 的空间范围，是 tiling 合法性校验的关键输入。
- [SetOutputPadding](set_output_padding.md)（`related`）：Conv3DTranspose 下 output padding 用于消除 stride 引起的输出尺寸歧义，不能独立设置。
- [SetPadding](set_padding.md)（`related`）：步长改变反卷积输出尺寸推导，需与前后/上下/左右 padding 一起满足 shape 公式。
<!-- cannbot:related:end -->
