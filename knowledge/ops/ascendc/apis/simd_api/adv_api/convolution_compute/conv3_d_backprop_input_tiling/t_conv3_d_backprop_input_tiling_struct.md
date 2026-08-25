---
type: API
title: TConv3DBackpropInputTiling结构体
description: TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput
  Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/TConv3DBackpropInputTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# TConv3DBackpropInputTiling结构体

TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`related`）：Kernel 对象消费该结构进行资源划分和迭代，形成 Host/Kernel 直接契约。
- [Conv3DBackpropInput Tiling构造函数](conv3_d_backprop_input_tiling_constructor.md)（`related`）：构造对象的最终产物写入 TConv3DBackpropInputTiling，Kernel 侧依赖该结构中的切分参数。
- [SetGradOutputType](set_grad_output_type.md)（`related`）：GradOutput 的位置、格式和 dtype 被序列化进结构并需与 Kernel 张量一致。
- [SetOutputPadding](set_output_padding.md)（`related`）：SetOutputPadding 与《TConv3DBackpropInputTiling结构体》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《TConv3DBackpropInputTiling结构体》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [卷积计算Init](../conv3_d_backprop_input_kernel/init.md)（`related`）：“卷积计算Init”定义：Init主要用于对Conv3DBackpropInput对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropInput Tiling侧接口。；“TConv3DBackpropInputTiling结构体”定义：TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。。实质衔接：Init 消费 Tiling 侧生成的结构并划分资源，是 Conv3DBackpropInput 使用流程的起点；计算完成还必须 End 释放事件和临时内存。
- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling.md)（`same_topic`）：tiling 总页定义该结构保存的规格字段和 Host 配置入口。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：TConv3DBackpropInputTiling结构体说明TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。
- [GetTiling](get_tiling.md)（`same_topic`）：GetTiling 把各 setter 收口并写入 TConv3DBackpropInputTiling。
<!-- cannbot:related:end -->
