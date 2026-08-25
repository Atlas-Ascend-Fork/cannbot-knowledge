---
type: API
title: SetWeightType
description: 设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/SetWeightType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeightType

设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。

函数原型：void SetWeightType(ConvCommonApi::TPosition pos, ConvCommonApi::ConvFormat format, ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Weight在内存上的位置。当前仅支持TPosition::GM。
- format（输入）：Weight的数据格式。当前仅支持ConvFormat::FRACTAL_Z_3D。
- dtype（输入）：Weight的数据类型。当前仅支持ConvDtype::FLOAT16或者ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [SetSingleWeightShape](../conv3_d_tiling/set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeightType》明确提供“设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightShape](set_weight_shape.md)（`related`）：SetWeightShape 与《SetWeightType》的实质衔接是：Weight shape 必须与 weight 类型、输入及 GradOutput 形状一起写入 Conv3DBackpropInput tiling 对象，再由 GetTiling 生成核侧结构。
- [SetWeight](../conv3_d_backprop_input_kernel/set_weight.md)（`same_topic`）：SetWeightType说明设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。
<!-- cannbot:related:end -->
