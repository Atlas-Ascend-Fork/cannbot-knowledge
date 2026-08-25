---
type: API
title: SetDilation
description: 设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetDilation.md
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

- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《Conv3DBackpropFilterTiling》说明提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [GetTiling](get_tiling.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《GetTiling》说明获取Tiling参数。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetDilation](../conv3_d_tiling/set_dilation.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《SetDilation》说明设置Dilation信息。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《TConv3DBpFilterTiling结构体》说明TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`same_topic`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《Conv3DBackpropFilter Tiling侧接口》说明提供Conv3D反向卷积滤波器梯度的Host侧Tiling接口，包含TConv3DBpFilterTiling结构体、GetTiling及形状与类型设置方法。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetDilation](../conv3_d_backprop_input_tiling/set_dilation.md)（`same_topic`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
<!-- cannbot:related:end -->
