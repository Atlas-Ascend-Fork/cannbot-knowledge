---
type: API
title: GetTiling
description: 获取Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetTiling

获取Tiling参数。

参数：
- tiling（输出）：Conv3D的Tiling结构体，用于存储最终的Tiling结果。TConv3DApiTiling结构介绍请参考TConv3DApiTiling结构体。

返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling构造函数](conv3d_tiling_constructor.md)（`related`）：构造并完成各项设置后必须调用 GetTiling 产出 TConv3DApiTiling，且返回 -1 时结果不可用，是同一对象生命周期的终点和验证条件。
- [SetGroups](set_groups.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetGroups》的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetOrgWeightShape](set_org_weight_shape.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《GetTiling》具体提供“获取Tiling参数。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetSingleWeightShape](set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《GetTiling》明确提供“获取Tiling参数。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [卷积计算Init](../conv3_d_kernel/init.md)（`related`）：Conv3D Host GetTiling 产出 TConv3DApiTiling，正是 Kernel Init 的 tiling 入参；GetTiling 失败时不能进入 Init。
- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`same_topic`）：《Conv3D Tiling使用说明》明确“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetTiling](../conv3_d_backprop_input_tiling/get_tiling.md)（`same_topic`）：《GetTiling》明确“获取Tiling参数。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《GetTiling》提供“获取Tiling参数。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
<!-- cannbot:related:end -->
