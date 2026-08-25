---
type: API
title: Conv3DBackpropInputTiling
description: 提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/Conv3DBackpropInput_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# Conv3DBackpropInputTiling

Ascend C提供一组Conv3DBackpropInput Tiling API，方便用户获取Conv3DBackpropInput Kernel计算时所需的Tiling参数。用户只需要传入Input/GradOutput/Weight的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DBackpropInputTiling结构体中的相关参数。 Conv3DBackpropInput Tiling API提供一个GetTiling接口获取Tiling参数，获取Tiling参数的流程如下：创建单核 Tiling 对象，设置 Input、GradOutput、Weight 的类型、Shape 及可选 Padding/Stride，最后调用 GetTiling。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：GetTiling 与《Conv3DBackpropInputTiling》的衔接是：GetTiling 是 Conv3DBackpropInput 主机侧配置的收口：构造并设置参数后生成 TConv3DBackpropInputTiling，随后由 Kernel 侧按该 tiling 驱动计算。
- [SetOutputPadding](set_output_padding.md)（`related`）：SetOutputPadding 与《Conv3DBackpropInputTiling》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetWeight](../conv3_d_backprop_input_kernel/set_weight.md)（`related`）：Conv3DBackpropInputTiling说明提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《Conv3DBackpropInputTiling》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [Conv3DBackpropInput](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_usage.md)（`same_topic`）：焦点处理Conv3DBackpropInput 的初始化、输入设置、迭代和取结果调用顺序；Conv3DBackpropInputTiling正文说明“提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息”。候选正是该用法页按先后调用的阶段；遗漏或错序会破坏资源划分、输入绑定或结果搬出。
- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`same_topic`）：Conv3DBackpropInputTiling说明提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息；对Conv3DBackpropInput Kernel侧接口而言，Host 侧生成的 TConv3DBackpropInputTiling 直接喂给 Kernel Init；Kernel 完成 Iterate 后必须用 GetTensorC 将 L0C 结果搬回 GM。
- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling.md)（`same_topic`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《Conv3DBackpropInputTiling》补充：提供获取Conv3DBackpropInput Kernel计算所需Tiling参数的API，用户传入输入输出参数后调用GetTiling接口获取Tiling信息。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《Conv3DBackpropInputTiling》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`same_topic`）：TConv3DBackpropInputTiling结构体说明TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。
- [卷积计算Init](../conv3_d_backprop_input_kernel/init.md)（`same_topic`）：卷积计算Init说明Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。
<!-- cannbot:related:end -->
