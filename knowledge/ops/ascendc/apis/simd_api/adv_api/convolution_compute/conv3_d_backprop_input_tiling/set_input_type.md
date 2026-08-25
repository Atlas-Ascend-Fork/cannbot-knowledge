---
type: API
title: SetInputType
description: 设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetInputType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetInputType

设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。

函数原型：void SetInputType(ConvCommonApi::TPosition pos, ConvCommonApi::ConvFormat format, ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Input在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Input的数据格式。当前仅支持ConvFormat::NDC1HWC0。
- dtype（输入）：Input的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：类型与形状 setter 最终由 GetTiling 固化为 Kernel 参数，是配置的直接消费端。
- [SetGradOutputType](set_grad_output_type.md)（`related`）：InputType 与 GradOutputType 共同描述反向输入两条数据路径，且都必须与 Kernel 侧类型一致。
- [SetInputShape](set_input_shape.md)（`related`）：SetInputShape 提供几何维度，SetInputType 提供存储与 dtype，两者共同构成完整 Input 描述。
- [SetInputType](../conv3_d_backprop_filter_tiling/set_input_type.md)（`related`）：输入梯度与滤波器梯度 tiling 都声明 Input 的位置、格式与 dtype；对照能避免把两类反向接口混用。
- [SetInputType](../conv3_d_tiling/set_input_type.md)（`related`）：正向 Conv3D 的 InputType 语义相近但对象和 tiling 结构不同；迁移时可对照而不能直接替换。
<!-- cannbot:related:end -->
