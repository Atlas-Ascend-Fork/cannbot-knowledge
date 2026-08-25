---
type: API
title: GetTiling
description: 获取Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetTiling

获取Tiling参数。

参数：
- tiling（输出）：TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考TConv3DBpFilterTiling结构体。

返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](../../../../../runbooks/compilation/get_tiling_data.md)（`exemplifies`）：GetTiling 与《GET_TILING_DATA 首参传类型名致变量遮蔽类型》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`related`）：Conv3DBackpropFilter Tiling侧接口 与《GetTiling》的实质衔接是：该 Host tiling 总览把构造、TConv3DBpFilterTiling、GetTiling 与 kernel/使用流程串成同一反向滤波器梯度契约；未为每个 setter 重复生成成员边。
- [Conv3DBackpropFilter Tiling构造函数](conv3_d_backprop_filter_tiling_constructor.md)（`related`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《GetTiling》说明获取Tiling参数。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`related`）：该流程在配置 Input、GradOutput、Weight、stride 与 padding 后以 GetTiling 产出 Kernel 所需参数，是指南的执行终点。
- [Conv3DBackpropFilter使用说明](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_usage.md)（`related`）：GetTiling 与《Conv3DBackpropFilter使用说明》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [GET_TILING_DATA](../../../basic_api/kernel_tiling/get_tiling_data.md)（`related`）：GetTiling 与《GET_TILING_DATA》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [GET_TILING_DATA_MEMBER](../../../basic_api/kernel_tiling/get_tiling_data_member.md)（`related`）：GetTiling 与《GET_TILING_DATA_MEMBER》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [GET_TILING_DATA_PTR_WITH_STRUCT](../../../basic_api/kernel_tiling/get_tiling_data_ptr_with_struct.md)（`related`）：GetTiling 与《GET_TILING_DATA_PTR_WITH_STRUCT》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [SetDilation](set_dilation.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《GetTiling》说明获取Tiling参数。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetInputShape](set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《GetTiling》说明获取Tiling参数。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 写入的权重维度会被随后调用的 GetTiling 消费，最终生成 TConv3DBpFilterTiling。
- [Conv3DBackpropFilter Kernel侧接口](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_kernel.md)（`same_topic`）：GetTiling 与《Conv3DBackpropFilter Kernel侧接口》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《GetTiling》的实质衔接是：该 setter 把 GradOutput 的 GM/NDC1HWC0 与 FP16/BF16 类型写入 BackpropFilter Host tiling；形状 setter 补齐同一张量描述，GetTiling 生成结构后由 kernel Init/SetGradOutput 按同一契约消费。
- [SetPadding](set_padding.md)（`same_topic`）：“SetPadding”处理void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)；“GetTiling”明确获取Tiling参数。。实质衔接：SetPadding 写入反向滤波 Tiling 对象的六向 padding，随后由 GetTiling 消费；使用说明给出这一步在 Host Tiling 调用序列中的位置。
- [SetWeightType](set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；GetTiling正文界定“获取Tiling参数”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`same_topic`）：GetTiling 与《TConv3DBpFilterTiling结构体》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
- [卷积计算Init](../conv3_d_backprop_filter_kernel/init.md)（`same_topic`）：GetTiling 与《卷积计算Init》的实质衔接是：GetTiling 在完成 BackpropFilter setter 配置后写出 TConv3DBpFilterTiling，供 kernel Init 消费；GET_TILING_DATA 宏与遮蔽故障说明 host 结果如何安全进入 device。
<!-- cannbot:related:end -->
