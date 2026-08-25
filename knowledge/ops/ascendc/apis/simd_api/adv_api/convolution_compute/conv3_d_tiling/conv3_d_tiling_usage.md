---
type: API
title: Conv3D Tiling使用说明
description: Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/Conv3D_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3D Tiling使用说明

Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。 Conv3D Tiling API提供Conv3D单核Tiling接口，用于Conv3D单核计算场景，获取Tiling参数的流程如下： 1. 创建一个单核Tiling对象。 2. 设置Input、Weight、Bias、Output的参数类型信息以及Shape信息，如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling构造函数](conv3d_tiling_constructor.md)（`related`）：使用说明把构造对象放入“创建对象、设置类型/Shape/卷积参数、再取 Tiling”的完整顺序，补足构造函数卡没有给出的生命周期。
- [SetDilation](set_dilation.md)（`related`）：The usage flow places SetDilation in the required Conv3D tiling initialization sequence before GetTiling.
- [SetOrgInputShape](set_org_input_shape.md)（`related`）：The Conv3D tiling flow requires original input shape alongside type, weight/output shapes, padding, stride, and dilation before GetTiling.
- [SetOutputType](set_output_type.md)（`related`）：《SetOutputType》的任务是“设置结果矩阵Output在内存上的位置、数据格式和数据类型。”。《Conv3D Tiling使用说明》具体提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，它直接用于Conv3D 输出位置/格式/dtype 在 Tiling 与 Kernel 间的一致性。
- [SetSingleOutputShape](../conv3_d_kernel/set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling使用说明》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [SetSingleWeightShape](set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》处理“设置单核上权重矩阵Weight的形状。”。《Conv3D Tiling使用说明》明确提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，其参数、调用或验证步骤直接接入Matmul 原始 weight 形状与 Tiling 类、结构体和 Kernel 设置接口的一致性。
- [SetWeightType](set_weight_type.md)（`related`）：SetWeightType 是 Conv3D Host tiling 初始化流程中的必需类型配置；使用说明明确它需与 Input/Bias/Output 类型及形状、stride/padding 等一起在 GetTiling 前设置。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《Conv3D Tiling使用说明》的“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling使用说明》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [GetTiling](get_tiling.md)（`same_topic`）：《Conv3D Tiling使用说明》明确“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”；它与《GetTiling》的“获取Tiling参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetGroups](set_groups.md)（`same_topic`）：《Conv3D Tiling使用说明》给出“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”；该约束/探针可直接复现、解释或前置验证《SetGroups》中的“设置分组卷积的分组大小。分组大小为1表示普通卷积。当前Conv3D高阶API不支持分组卷积。”。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling使用说明》提供“Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
<!-- cannbot:related:end -->
