---
type: API
title: Conv3DBackpropFilterTiling
description: 提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/Conv3DBackpropFilter_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# Conv3DBackpropFilterTiling

Ascend C提供一组Conv3DBackpropFilter Tiling API，方便用户获取Conv3DBackpropFilter Kernel计算时所需的Tiling参数。用户只需要传入Input/GradOutput/GradWeight的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DBpFilterTiling结构体中的相关参数。 Conv3DBackpropFilter Tiling API提供一个GetTiling接口获取Tiling参数，获取Tiling参数的流程如下：创建单核 Tiling 对象，设置 Input、GradOutput、GradWeight 的类型、Shape 及可选 Padding/Stride，最后调用 GetTiling。

<!-- cannbot:related:start -->
## 相关

- [errcode 82 — streamk stepK 致 L1 越界](../../../../../runbooks/compilation/conv3d_bp_filter_v2_streamk_stepk_l1_overflow_errcode_82.md)（`exemplifies`）：Tiling 使用说明给出 Host 配置与 GetTiling 的完整路径，可在 stepK 后重新执行 L1 合法性校验并观察错误码。
- [Conv3DBackpropFilter使用说明](../conv3_d_backprop_filter_kernel/conv3_d_backprop_filter_usage.md)（`related`）：Kernel 使用说明消费 Host GetTiling 生成的结构并给出 Init、Iterate、GetTensorC 顺序，闭合 Host 到 Device 契约。
- [GetTiling](get_tiling.md)（`related`）：该流程在配置 Input、GradOutput、Weight、stride 与 padding 后以 GetTiling 产出 Kernel 所需参数，是指南的执行终点。
- [SetDilation](set_dilation.md)（`related`）：《SetDilation》说明设置Dilation信息，即卷积核Depth/Height/Width方向的扩张大小。；《Conv3DBackpropFilterTiling》说明提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。二者在Dilation是Conv3D反向滤波Tiling的卷积几何参数，必须在GetTiling前写入并与同语义的前向/反向输入配置区分上存在可执行的直接衔接。
- [SetInputShape](set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《Conv3DBackpropFilterTiling》说明提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：使用说明给出从 Host 侧配置、GetTiling 到 Kernel 侧消费该结构体的完整传递流程。
- [Conv3DBackpropFilter Tiling构造函数](conv3_d_backprop_filter_tiling_constructor.md)（`same_topic`）：《Conv3DBackpropFilter Tiling构造函数》说明用于创建一个Conv3DBackpropFilter单核Tiling对象。；《Conv3DBackpropFilterTiling》说明提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。二者在构造函数接收的平台对象、SoC版本和各级存储容量必须与后续GetTiling生成的反向滤波Tiling结构一致上存在可执行的直接衔接。
- [SetGradOutputShape](set_grad_output_shape.md)（`same_topic`）：使用说明给出 SetGradOutputShape 在完整参数配置序列中的位置，并说明其结果如何进入 GetTiling。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《Conv3DBackpropFilterTiling》的实质衔接是：该 setter 把 GradOutput 的 GM/NDC1HWC0 与 FP16/BF16 类型写入 BackpropFilter Host tiling；形状 setter 补齐同一张量描述，GetTiling 生成结构后由 kernel Init/SetGradOutput 按同一契约消费。
- [SetInputType](set_input_type.md)（`same_topic`）：使用说明给出 SetInputType 在完整 BackpropFilter tiling 配置序列中的位置及其到 GetTiling 的衔接。
- [SetPadding](set_padding.md)（`same_topic`）：“SetPadding”处理void SetPadding(int64_t padFront, int64_t padBack, int64_t padUp, int64_t padDown, int64_t padLeft, int64_t padRight)；“Conv3DBackpropFilterTiling”明确提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。。实质衔接：SetPadding 写入反向滤波 Tiling 对象的六向 padding，随后由 GetTiling 消费；使用说明给出这一步在 Host Tiling 调用序列中的位置。
- [SetStride](set_stride.md)（`same_topic`）：使用流程要求依次设置输入输出、类型、padding 与 stride 后再 GetTiling，SetStride 正是该调用链的 stride 环节。
- [SetWeightShape](set_weight_shape.md)（`same_topic`）：Tiling 使用流程要求依次设置 Input、GradOutput、GradWeight 的类型和 Shape 后再调用 GetTiling，SetWeightShape 正是其中的权重形状步骤。
- [SetWeightType](set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；Conv3DBackpropFilterTiling正文界定“提供获取Conv3DBackpropFilter Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
<!-- cannbot:related:end -->
