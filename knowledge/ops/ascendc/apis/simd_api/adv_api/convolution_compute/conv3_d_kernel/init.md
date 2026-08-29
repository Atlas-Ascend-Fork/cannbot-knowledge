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

- [Conv3D Tiling使用说明](../conv3_d_tiling/conv3_d_tiling_usage.md)（`related`）：Ascend C提供一组Conv3D Tiling API，方便用户获取Conv3D正向算子Kernel计算时所需的Tiling参数。用户只需要传入Input/Weight/Bias/Output的Position位置、Format格式和DType数据类型及相关参数等信息，调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。 Conv3D Tiling API提供Conv3D单核Tiling接口，用于Conv3D单核计算场景，获取Tiling参数的流程如下： 1. 创建一个单核Tiling对象。 2. 设置Input、Weight、Bias、Output的参数类型信息以及Shape信息，如果存在Padding、Stride、Dilation参数，通过SetPadding、SetStride、SetDilation接口进行相关设置。；参数： - cubeTiling（输入）：Conv3D对象的Tiling参数，Tiling结构体定义请参见TConv3DApiTiling结构体。 Tiling参数可以通过Host侧GetTiling接口获取，并传递到Kernel侧使用。；焦点描述 Host 侧参数获取，目标明确同一结构体通过 Init 进入 Kernel 并触发资源划分。
- [GetTiling](../conv3_d_tiling/get_tiling.md)（`related`）：焦点卡规定“Tiling参数可以通过Host侧GetTiling接口获取，并传递到Kernel侧使用”，候选卡说明“如果返回值不为-1，则代表Tiling计算成功”；两卡组成 Host 生成并校验 Tiling、再交给 Kernel Init 的直接参数链。
- [IterateAll](iterate_all.md)（`related`）：焦点卡要求“Init接口必须在IterateAll和End接口前调用”，候选卡再次约束“IterateAll接口必须在初始化接口及输入输出配置接口之后进行调用”；两端共同固定 Conv3D Kernel 的初始化到计算阶段顺序。
<!-- cannbot:related:end -->
