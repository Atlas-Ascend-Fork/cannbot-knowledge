---
type: API
title: Conv3DUsage
description: Ascend C提供Conv3D高阶API，用于快速实现3维卷积正向矩阵运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3D_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3DUsage

Ascend C提供一组Conv3D高阶API，方便用户快速实现3维卷积正向矩阵运算。3维正向卷积的示意图如图1，其计算公式为： - X为Conv3D卷积的特征矩阵Input。 - W为Conv3D卷积的权重矩阵Weight。 - B为Conv3D卷积的偏置矩阵Bias。 - Y为完成卷积及偏置操作之后的结果矩阵Output。 图1 3维正向卷积示意图

<!-- cannbot:related:start -->
## 相关

- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3DUsage》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [TConv3DApiTiling结构体](../conv3_d_tiling/t_conv3_d_api_tiling_struct.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3DUsage》提供“Ascend C提供Conv3D高阶API，用于快速实现3维卷积正向矩阵运算。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Kernel侧接口](conv3d_kernel.md)（`same_topic`）：使用页串起 Conv3D 对象 Init、SetInput/Weight、IterateAll 和 End。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《Conv3DUsage》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《Conv3DUsage》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
<!-- cannbot:related:end -->
