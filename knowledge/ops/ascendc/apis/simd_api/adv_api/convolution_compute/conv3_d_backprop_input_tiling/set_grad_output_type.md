---
type: API
title: SetGradOutputType
description: 设置GradOutput的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetGradOutputType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetGradOutputType

设置GradOutput的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。

函数原型：void SetGradOutputType(ConvCommonApi::TPosition pos, ConvCommonApi::ConvFormat format, ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：GradOutput在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：GradOutput的数据格式。当前仅支持ConvFormat::NDC1HWC0。
- dtype（输入）：GradOutput的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [SetInputType](set_input_type.md)（`related`）：InputType 与 GradOutputType 共同描述反向输入两条数据路径，且都必须与 Kernel 侧类型一致。
- [TConv3DBackpropInputTiling结构体](t_conv3_d_backprop_input_tiling_struct.md)（`related`）：GradOutput 的位置、格式和 dtype 被序列化进结构并需与 Kernel 张量一致。
- [Conv3DBackpropInputTiling](conv3_d_backprop_input_tiling_usage.md)（`same_topic`）：SetGradOutputType 与《Conv3DBackpropInputTiling》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [GetTiling](get_tiling.md)（`same_topic`）：SetGradOutputType 与《GetTiling》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [SetGradOutput](../conv3_d_backprop_input_kernel/set_grad_output.md)（`same_topic`）：SetGradOutputType 与《SetGradOutput》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [SetGradOutputShape](set_grad_output_shape.md)（`same_topic`）：SetGradOutputType 与《SetGradOutputShape》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [SetGradOutputType](../conv3_d_backprop_filter_tiling/set_grad_output_type.md)（`same_topic`）：SetGradOutputType 与《SetGradOutputType》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
- [卷积计算Init](../conv3_d_backprop_input_kernel/init.md)（`same_topic`）：SetGradOutputType 与《卷积计算Init》的实质衔接是：主机侧 GradOutput 的 GM/NDC1HWC0/dtype 设置必须与实际 SetGradOutput 张量及 Kernel Init 消费的 tiling 数据一致；shape、GetTiling 和 tiling struct 完成同一配置链。
<!-- cannbot:related:end -->
