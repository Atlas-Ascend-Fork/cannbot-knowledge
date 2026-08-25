---
type: API
title: SetInputType
description: 设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetInputType.md
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

- [SetInput](../conv3_d_backprop_filter_kernel/set_input.md)（`related`）：Host 侧设置的 GM、NDC1HWC0 与 dtype 必须和 Kernel 侧 SetInput 绑定的 GlobalTensor 保持一致。
- [SetInputShape](set_input_shape.md)（`related`）：《SetInputShape》说明设置特征矩阵Input的形状：Batch、Channel、Depth、Height、Width。；《SetInputType》说明设置特征矩阵Input的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。。二者在Host Tiling中的Input原始shape必须与同类反向卷积Tiling对象、类型配置、GetTiling产物及Kernel侧SetInput合同一致上存在可执行的直接衔接。
- [SetInputType](../conv3_d_backprop_input_tiling/set_input_type.md)（`related`）：输入梯度与滤波器梯度 tiling 都声明 Input 的位置、格式与 dtype；对照能避免把两类反向接口混用。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：使用说明给出 SetInputType 在完整 BackpropFilter tiling 配置序列中的位置及其到 GetTiling 的衔接。
<!-- cannbot:related:end -->
