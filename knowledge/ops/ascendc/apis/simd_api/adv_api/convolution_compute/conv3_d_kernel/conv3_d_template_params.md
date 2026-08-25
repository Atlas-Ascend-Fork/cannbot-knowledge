---
type: API
title: Conv3D模板参数
description: 创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。
  - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3D_template_params.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D模板参数

创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。

函数原型：template <class INPUT_TYPE, class WEIGHT_TYPE, class OUTPUT_TYPE, class BIAS_TYPE = biasType, class CONV_CFG = Conv3dParam>

参数：
- INPUT_TYPE（输入）：ConvType类型模板参数，指定Input的参数类型信息。
- WEIGHT_TYPE（输入）：ConvType类型模板参数，指定Weight的参数类型信息。
- OUTPUT_TYPE（输入）：ConvType类型模板参数，指定Output的参数类型信息。
- BIAS_TYPE（可选输入）：ConvType类型模板参数，指定Bias的参数类型信息。
- CONV_CFG（可选输入）：ConvParam类型模板参数，用于开启不同场景的性能优化模板，当前版本只支持基础模板，不开启性能优化。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3D模板参数》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [TConv3DApiTiling结构体](../conv3_d_tiling/t_conv3_d_api_tiling_struct.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D模板参数》提供“创建Conv3D对象时需要传入： - Input、Weight、Output和Bias（可选）的参数类型信息，类型信息通过ConvType来定义，包括：内存逻辑位置、数据格式、数据类型。 - Conv3dParam信息（可选），用于开启不同场景的性能优化模板。当前暂不支持使用。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Kernel侧接口](conv3d_kernel.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Kernel侧接口》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [Conv3D Tiling使用说明](../conv3_d_tiling/conv3_d_tiling_usage.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling使用说明》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [Conv3D Tiling侧接口](../conv3_d_tiling/conv3d_tiling.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling侧接口》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [Conv3D Tiling构造函数](../conv3_d_tiling/conv3d_tiling_constructor.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling构造函数》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [Conv3DUsage](conv3_d_usage.md)（`same_topic`）：Conv3D模板参数 与《Conv3DUsage》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetBias](set_bias.md)（`same_topic`）：Conv3D模板参数 与《SetBias》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetBiasType](../conv3_d_tiling/set_bias_type.md)（`same_topic`）：Conv3D模板参数 与《SetBiasType》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetGroups](../conv3_d_tiling/set_groups.md)（`same_topic`）：Conv3D模板参数 与《SetGroups》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetInput](set_input.md)（`same_topic`）：Conv3D模板参数 与《SetInput》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetWeight](set_weight.md)（`same_topic`）：Conv3D模板参数 与《SetWeight》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [SetWeightType](../conv3_d_tiling/set_weight_type.md)（`same_topic`）：Conv3D模板参数 与《SetWeightType》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《Conv3D模板参数》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：Conv3D模板参数 与《卷积计算Init》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [模板参数定义](../../../../utils_api/tiling_template_programming/template_params_definition.md)（`same_topic`）：Conv3D模板参数 与《模板参数定义》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
<!-- cannbot:related:end -->
