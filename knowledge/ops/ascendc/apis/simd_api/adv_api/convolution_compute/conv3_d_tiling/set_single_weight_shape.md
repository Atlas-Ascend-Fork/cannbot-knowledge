---
type: API
title: SetSingleWeightShape
description: 设置单核上权重矩阵Weight的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetSingleWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleWeightShape

设置单核上权重矩阵Weight的形状。

函数原型：void SetSingleWeightShape(int64_t singleCi, int64_t singleKd, int64_t singleKh, int64_t singleKw)

参数：
- singleCi（输入）：单核上输入通道的大小。
- singleKd（输入）：单核上Weight D维度大小。
- singleKh（输入）：单核上Weight H维度大小。
- singleKw（输入）：单核上Weight W维度大小。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《Conv3D Tiling使用说明》明确提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《Conv3D Tiling侧接口》明确提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [GetTiling](get_tiling.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《GetTiling》明确提供“获取Tiling参数。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetOrgWeightShape](set_org_weight_shape.md)（`related`）：《SetSingleWeightShape》明确“设置单核上权重矩阵Weight的形状。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetWeight](../conv3_d_backprop_input_kernel/set_weight.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeight》明确提供“设置卷积反向计算的输入矩阵Weight。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeight](../conv3_d_kernel/set_weight.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeight》明确提供“设置权重矩阵Weight。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](../conv3_d_backprop_filter_tiling/set_weight_type.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeightType》明确提供“设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](../conv3_d_backprop_input_tiling/set_weight_type.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeightType》明确提供“设置权重矩阵Weight的位置、数据格式、数据类型信息，这些信息必须与Kernel侧的设置保持一致。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《TConv3DApiTiling结构体》明确提供“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](set_weight_type.md)（`same_topic`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《SetWeightType》明确提供“设置Weight在内存上的位置、数据格式和数据类型。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
<!-- cannbot:related:end -->
