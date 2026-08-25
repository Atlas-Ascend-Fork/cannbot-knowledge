---
type: API
title: 卷积计算Init
description: Init主要用于对Conv3D对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，同时获取用户声明的Pipe对象，完成内存分配。Tiling参数的具体介绍请参考Conv3D
  Tiling。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Kernel/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 卷积计算Init

Init主要用于对Conv3D对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，同时获取用户声明的Pipe对象，完成内存分配。Tiling参数的具体介绍请参考Conv3D Tiling。

函数原型：__aicore__ inline void Init(const void* __restrict cubeTiling)

参数：
- cubeTiling（输入）：Conv3D对象的Tiling参数，Tiling结构体定义请参见TConv3DApiTiling结构体。 Tiling参数可以通过Host侧GetTiling接口获取，并传递到Kernel侧使用。

约束：
- 调用Init接口前必须先初始化TPipe。
- Init接口必须在IterateAll和End接口前调用，且只能调用一次Init接口，调用顺序如下。 IterateAll(...);

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](../conv3_d_tiling/get_tiling.md)（`related`）：Conv3D Host GetTiling 产出 TConv3DApiTiling，正是 Kernel Init 的 tiling 入参；GetTiling 失败时不能进入 Init。
- [IterateAll](iterate_all.md)（`related`）：Init 建立 Conv3D Kernel 对象状态后，IterateAll 才执行完整卷积计算，二者构成明确的初始化—执行顺序。
- [SetSingleOutputShape](set_single_output_shape.md)（`related`）：SetSingleOutputShape 与《卷积计算Init》的实质衔接是：SetSingleOutputShape 定义单核 Co/Do/M 输出分块；Conv3D kernel、tiling、shape 查询与 Iterate 的参数必须按同一 M 合轴输出契约传递。
- [TConv3DApiTiling结构体](../conv3_d_tiling/t_conv3_d_api_tiling_struct.md)（`related`）：《TConv3DApiTiling结构体》处理“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。”。《卷积计算Init》提供“Init主要用于对Conv3D对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，同时获取用户声明的Pipe对象，完成内存分配。Tiling参数的具体介绍请参考Conv3D Tiling。”，其具体合同或探针直接接入Conv3D 前向 Tiling 结构的构造、Host 求解、Kernel Init 与类型参数合同。
- [Conv3D Kernel侧接口](conv3d_kernel.md)（`same_topic`）：Init 消费 Host Tiling 并划分内部资源，是对象使用的起点。
- [Conv3D模板参数](conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《卷积计算Init》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [卷积计算End](end.md)（`same_topic`）：卷积计算End 与《卷积计算Init》的实质衔接是：Conv3D 完成 Iterate/GetTensorC 后必须调用 End 清理 EventID 和内部临时内存；Init、模板、usage 及其他卷积 End 入口共享这一成对生命周期。
<!-- cannbot:related:end -->
