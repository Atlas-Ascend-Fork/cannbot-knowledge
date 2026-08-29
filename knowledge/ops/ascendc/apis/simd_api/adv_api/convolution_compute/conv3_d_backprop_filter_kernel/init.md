---
type: API
title: 卷积计算Init
description: Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropFilter
  Tiling侧接口。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Kernel/Init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# 卷积计算Init

Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropFilter Tiling侧接口。

函数原型：__aicore__ inline void Init(const TConv3DBpFilterTiling* __restrict tiling)

参数：
- tiling（输入）：Conv3DBackpropFilter对象的Tiling参数，Conv3DBackpropFilterTilingData结构体定义请参见TConv3DBpFilterTiling结构体。 。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](../conv3_d_backprop_filter_tiling/get_tiling.md)（`related`）：“- tiling（输出）：TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考TConv3DBpFilterTiling结构体。”与“Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分，Tiling参数的具体介绍请参考Conv3DBackpropFilter Tiling侧接口。”。Tiling 接口生产 TConv3DBpFilterTiling，Kernel Init 消费它完成资源划分。
- [Iterate（卷积计算）](iterate.md)（`related`）：“Init主要用于对Conv3DBackpropFilter对象中的Tiling数据进行初始化，根据Tiling参数进行资源划分”建立对象和资源；“Iterate接口必须在初始化接口及输入输出配置接口之后进行调用，完成卷积反向实现”明确计算阶段依赖初始化，形成同一调用序列。
<!-- cannbot:related:end -->
