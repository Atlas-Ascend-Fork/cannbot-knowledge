---
type: API
title: GetTiling
description: 获取Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetTiling

获取Tiling参数。

参数：
- tiling（输出）：Conv3DBackpropInput的Tiling结构体，用于存储最终的Tiling结果。TConv3DBackpropInputTiling结构介绍请参考TConv3DApiTiling结构体说明。

返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`related`）：GetTiling 与《Conv3DBackpropInput Kernel侧接口》的衔接是：GetTiling 是 Conv3DBackpropInput 主机侧配置的收口：构造并设置参数后生成 TConv3DBackpropInputTiling，随后由 Kernel 侧按该 tiling 驱动计算。
- [Conv3DBackpropInput Tiling侧接口](conv3_d_backprop_input_tiling.md)（`related`）：Conv3DBackpropInput Tiling侧接口：该 Host Tiling集合产出 TConv3DBackpropInputTiling，GetTiling把形状/类型/卷积参数固化后交给同算子的 Kernel Init；用法卡展示完整 Host→Kernel 衔接。 目标卡《GetTiling》补充：获取Tiling参数。
- [Conv3DBackpropInput Tiling构造函数](conv3_d_backprop_input_tiling_constructor.md)（`related`）：构造函数创建单核 tiling 对象；配置 shape/type/stride 后必须调用 GetTiling 才生成传给 Kernel 的结构体。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`related`）：GetTiling 与《Conv3DBackpropInputTiling》的衔接是：GetTiling 是 Conv3DBackpropInput 主机侧配置的收口：构造并设置参数后生成 TConv3DBackpropInputTiling，随后由 Kernel 侧按该 tiling 驱动计算。
- [SetGradOutputShape](set_grad_output_shape.md)（`related`）：SetGradOutputShape 等 setter 的结果最终由 GetTiling 汇总生成 Kernel 参数；缺少该调用配置不会形成可用 tiling。
- [SetInputType](set_input_type.md)（`related`）：类型与形状 setter 最终由 GetTiling 固化为 Kernel 参数，是配置的直接消费端。
- [SetOutputPadding](set_output_padding.md)（`related`）：SetOutputPadding 与《GetTiling》的实质衔接是：SetOutputPadding 只在 Conv3DTranspose 形状反推中生效；这些卡共同限定输入、普通 padding、tiling 结构与 GetTiling/Init 的调用链，并用同名属性非根因案例防止误诊。
- [SetStride](set_stride.md)（`related`）：SetStride 等几何配置最终由 GetTiling 固化为 Kernel 参数。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《GetTiling》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [GetTiling](../conv3_d_tiling/get_tiling.md)（`same_topic`）：《GetTiling》明确“获取Tiling参数。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetGradOutputType](set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《GetTiling》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`same_topic`）：GetTiling 把各 setter 收口并写入 TConv3DBackpropInputTiling。
<!-- cannbot:related:end -->
