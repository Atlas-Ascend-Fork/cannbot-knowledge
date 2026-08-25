---
type: API
title: TConv3DBpFilterTiling结构体
description: TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter
  Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/TConv3DBpFilterTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# TConv3DBpFilterTiling结构体

TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DBpFilterTiling结构体，具体流程请参考使用说明。当前暂不支持用户自定义配置TConv3DBpFilterTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。

<!-- cannbot:related:start -->
## 相关

- [errcode 82 — streamk stepK 致 L1 越界](../../../../../runbooks/compilation/conv3d_bp_filter_v2_streamk_stepk_l1_overflow_errcode_82.md)（`exemplifies`）：该结构承载 stepKa/stepKb、L1 bounds 与单核切分结果，正是复现 streamk 限制后 L1 容量不一致需要检查的 tiling 状态。
- [Conv3DBackpropFilter Kernel侧接口](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_kernel.md)（`related`）：Conv3DBackpropFilter Kernel 以该 Tiling 结构驱动切分、搬运和计算，是结构体的直接消费者。
- [Conv3DBackpropFilter Tiling构造函数](conv3_d_backprop_filter_tiling_constructor.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《TConv3DBpFilterTiling结构体》说明TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`related`）：使用说明给出从 Host 侧配置、GetTiling 到 Kernel 侧消费该结构体的完整传递流程。
- [Conv3DBackpropFilter使用说明](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_usage.md)（`related`）：Conv3DBackpropFilter使用说明 与《TConv3DBpFilterTiling结构体》的实质衔接是：该使用说明直接串联 BackpropFilter 的 host tiling、kernel Init/Iterate/End、输入与 grad-output 设置及结果获取。
- [SetDilation](set_dilation.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《TConv3DBpFilterTiling结构体》说明TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetInputShape](set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《TConv3DBpFilterTiling结构体》说明TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [SetStride](set_stride.md)（`related`）：SetStride 写入的卷积步长参与生成 TConv3DBpFilterTiling，目标结构体是 Kernel 侧消费这组 Tiling 结果的契约。
- [SetWeightShape](set_weight_shape.md)（`related`）：TConv3DBpFilterTiling 承载由权重、输入和梯度输出规格计算出的切分结果，是 SetWeightShape 配置在 Kernel 侧生效的下游载体。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`same_topic`）：Conv3DBackpropFilter Tiling侧接口 与《TConv3DBpFilterTiling结构体》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
- [GetTiling](get_tiling.md)（`same_topic`）：GetTiling 与《TConv3DBpFilterTiling结构体》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [SetWeightType](set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；TConv3DBpFilterTiling结构体正文界定“TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TC”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
<!-- cannbot:related:end -->
