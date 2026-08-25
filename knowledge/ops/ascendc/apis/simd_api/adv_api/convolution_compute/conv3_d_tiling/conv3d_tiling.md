---
type: API
title: Conv3D Tiling侧接口
description: 提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/Conv3d_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D Tiling侧接口

提供 Conv3D 前向计算的 Host 侧 Tiling 接口，通过 TConv3DApiTiling 结构体承载切分参数。
核心方法 GetTiling 用于获取最终 Tiling 数据；SetOrgWeightShape/SetOrgInputShape 设置原始权重与输入形状，SetSingleWeightShape/SetSingleOutputShape 设置单次计算形状。
另提供 SetInputType/SetWeightType/SetBiasType/SetOutputType 设置数据类型，SetPadding/SetDilation/SetStride/SetGroups 设置卷积超参数。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Kernel侧接口](../conv3_d_kernel/conv3d_kernel.md)（`related`）：Conv3D tiling 侧汇总的 shape、dtype、padding、stride 等配置最终生成 TConv3DApiTiling，kernel 侧接口消费该结构完成前向卷积。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《Conv3D Tiling侧接口》具体提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetSingleOutputShape](../conv3_d_kernel/set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling侧接口》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [SetSingleWeightShape](set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《Conv3D Tiling侧接口》明确提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《Conv3D Tiling使用说明》的“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling侧接口》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [GetTiling](get_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetGroups](set_groups.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetGroups》的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetOrgWeightShape](set_org_weight_shape.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetSingleOutputShape](set_single_output_shape.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling侧接口》提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
<!-- cannbot:related:end -->
