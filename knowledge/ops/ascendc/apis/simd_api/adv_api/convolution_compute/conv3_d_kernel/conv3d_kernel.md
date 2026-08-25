---
type: API
title: Conv3D Kernel侧接口
description: 提供Conv3D前向计算的Kernel侧接口，包含Init、SetInput、SetWeight、IterateAll等方法及模板参数与使用说明。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Conv3d_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D Kernel侧接口

提供三维卷积前向计算的 Kernel 侧接口，基于模板参数配置输入、权重、偏置的数据类型与排布格式。
核心方法包括 Init 初始化、SetInput/SetWeight/SetBias 设置输入张量、SetSingleOutputShape 设置单次输出形状、SetInputStartPosition 设置输入起始位置、IterateAll 执行全部迭代、End 释放资源。
使用前需通过模板参数指定 TPosition、数据类型及 Layout 等配置，具体约束参见 Conv3D 使用说明。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling侧接口](../conv3_d_tiling/conv3d_tiling.md)（`related`）：Conv3D tiling 侧汇总的 shape、dtype、padding、stride 等配置最终生成 TConv3DApiTiling，kernel 侧接口消费该结构完成前向卷积。
- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《Conv3D Kernel侧接口》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [TConv3DApiTiling结构体](../conv3_d_tiling/t_conv3_d_api_tiling_struct.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《Conv3D Kernel侧接口》提供“提供Conv3D前向计算的Kernel侧接口，包含Init、SetInput、SetWeight、IterateAll等方法及模板参数与使用说明。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3DUsage](conv3_d_usage.md)（`same_topic`）：使用页串起 Conv3D 对象 Init、SetInput/Weight、IterateAll 和 End。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《Conv3D Kernel侧接口》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [IterateAll](iterate_all.md)（`same_topic`）：Kernel 对象页定义 IterateAll 所属生命周期。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《Conv3D Kernel侧接口》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
- [卷积计算Init](init.md)（`same_topic`）：Init 消费 Host Tiling 并划分内部资源，是对象使用的起点。
<!-- cannbot:related:end -->
