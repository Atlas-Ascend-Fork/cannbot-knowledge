---
type: API
title: TConv3DApiTiling结构体
description: TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/TConv3DApiTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# TConv3DApiTiling结构体

TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DApiTiling结构体，具体流程请参考Conv3D Tiling使用说明。当前暂不支持用户自定义配置TConv3DApiTiling结构体中的参数。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Kernel侧接口](../conv3_d_kernel/conv3d_kernel.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Kernel侧接口》提供“提供Conv3D前向计算的Kernel侧接口，包含Init、SetInput、SetWeight、IterateAll等方法及模板参数与使用说明。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3DUsage](../conv3_d_kernel/conv3_d_usage.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3DUsage》提供“Ascend C提供Conv3D高阶API，用于快速实现3维卷积正向矩阵运算。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D模板参数》提供“创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《TConv3DApiTiling结构体》具体提供“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetSingleWeightShape](set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《TConv3DApiTiling结构体》明确提供“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [卷积计算Init](../conv3_d_kernel/init.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《卷积计算Init》提供“Init主要用于对Conv3D对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，同时获取用户声明的Pipe对象，完成内存分配。Tiling参数的具体介绍请参考Conv3D Tiling。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling使用说明》提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling侧接口》提供“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Tiling构造函数](conv3d_tiling_constructor.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling构造函数》提供“用于创建一个Conv3D单核Tiling对象。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [GetTiling](get_tiling.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《GetTiling》提供“获取Tiling参数。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
<!-- cannbot:related:end -->
