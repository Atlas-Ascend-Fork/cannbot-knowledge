---
type: API
title: SetDilation
description: 设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetDilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetDilation

设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。

函数原型：void SetDilation(int64_t dilationD, int64_t dilationH, int64_t dilationW)

参数：
- dilationD（输入）：卷积核Weight的Depth方向扩张大小。
- dilationH（输入）：卷积核Weight的Height方向扩张大小。
- dilationW（输入）：卷积核Weight的Width方向扩张大小。

<!-- cannbot:related:start -->
## 相关

- [SetStride](set_stride.md)（`related`）：Stride 与 Dilation 共同决定 GradOutput 到 Input 的采样几何，Host 侧必须以同一 D/H/W 轴序配置。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetDilation 的三个扩张量直接作用于 Weight 的 D/H/W 核尺寸；SetWeightShape 提供这三个原始尺寸，二者共同决定反向输入卷积的有效核范围。
- [SetDilation](../conv3_d_backprop_filter_tiling/set_dilation.md)（`same_topic`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
<!-- cannbot:related:end -->
