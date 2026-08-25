---
type: API
title: SetStride
description: 设置Stride信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetStride.md
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

- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：SetStride 写入的卷积步长参与生成 TConv3DBpFilterTiling，目标结构体是 Kernel 侧消费这组 Tiling 结果的契约。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`same_topic`）：Conv3DBackpropFilter Tiling 总览把 SetStride 列为 Host 侧构造反向滤波 Tiling 参数的设置步骤。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：使用流程要求依次设置输入输出、类型、padding 与 stride 后再 GetTiling，SetStride 正是该调用链的 stride 环节。
<!-- cannbot:related:end -->
