---
type: API
title: SetOutputType
description: 设置结果矩阵Output在内存上的位置、数据格式和数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetOutputType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetOutputType

设置结果矩阵Output在内存上的位置、数据格式和数据类型。

函数原型：void SetOutputType(const ConvCommonApi::TPosition pos, const ConvCommonApi::ConvFormat format, const ConvCommonApi::ConvDtype dtype)

参数：
- pos（输入）：Output在内存上的位置。当前仅支持TPosition::CO1。
- format（输入）：Output的数据格式。当前仅支持ConvFormat::NDC1HWC0。
- dtype（输入）：Output的数据类型。当前仅支持ConvDtype::FLOAT16、ConvDtype::BF16。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《Conv3D Tiling使用说明》具体提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《Conv3D Tiling侧接口》具体提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [GetTiling](get_tiling.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《GetTiling》具体提供“获取Tiling参数。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetBiasType](set_bias_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetBiasType》具体提供“设置Bias在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetInputType](set_input_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetInputType》具体提供“设置Input在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetWeightType](set_weight_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《SetWeightType》具体提供“设置Weight在内存上的位置、数据格式和数据类型。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《TConv3DApiTiling结构体》具体提供“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
<!-- cannbot:related:end -->
