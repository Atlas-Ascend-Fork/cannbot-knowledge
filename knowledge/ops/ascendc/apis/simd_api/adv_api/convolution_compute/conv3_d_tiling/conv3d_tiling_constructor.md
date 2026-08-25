---
type: API
title: Conv3D Tiling构造函数
description: 用于创建一个Conv3D单核Tiling对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/Conv3d_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# Conv3D Tiling构造函数

用于创建一个Conv3D单核Tiling对象。

参数：
- ascendcPlatform（输入）：传入硬件平台的信息，PlatformAscendC定义请参见构造及析构函数。
- platform（输入）：传入硬件版本以及AI Core中各个硬件单元提供的内存大小。PlatformInfo构造时通过构造及析构函数获取。 PlatformInfo结构定义如下方代码所示，socVersion通过GetSocVersion获取并透传，各类硬件存储空间大小通过GetCoreMemSize获取并透传。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：使用说明把构造对象放入“创建对象、设置类型/Shape/卷积参数、再取 Tiling”的完整顺序，补足构造函数卡没有给出的生命周期。
- [GetTiling](get_tiling.md)（`related`）：构造并完成各项设置后必须调用 GetTiling 产出 TConv3DApiTiling，且返回 -1 时结果不可用，是同一对象生命周期的终点和验证条件。
- [SetSingleOutputShape](../conv3_d_kernel/set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3D Tiling构造函数》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [Conv3D模板参数](../conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Tiling构造函数》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [TConv3DApiTiling结构体](t_conv3_d_api_tiling_struct.md)（`same_topic`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Tiling构造函数》提供“用于创建一个Conv3D单核Tiling对象。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
<!-- cannbot:related:end -->
