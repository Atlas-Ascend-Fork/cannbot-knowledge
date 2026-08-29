---
type: API
title: TConv3DBackpropInputTiling结构体
description: TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput
  Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropInput_Tiling/TConv3DBackpropInputTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# TConv3DBackpropInputTiling结构体

TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。

<!-- cannbot:related:start -->
## 相关

- [Conv3DBackpropInput Kernel侧接口](../conv3_d_backprop_input_kernel/conv3_d_backprop_input_kernel.md)（`related`）：核心方法包括 Init 初始化、SetGradOutput 设置梯度输出、SetWeight 设置权重、SetSingleShape 设置单次计算形状、SetStartPosition 设置起始位置、Iterate 执行迭代、GetTensorC 获取结果、End 释放资源。；TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。。结构体卡明确参数被传给 Kernel，Kernel 卡给出消费这些参数的初始化与迭代生命周期。
- [GetTiling](get_tiling.md)（`related`）：TConv3DBackpropInputTiling结构体包含Conv3DBackpropInput算子规格信息及Tiling切分算法的相关参数，被传递给Conv3DBackpropInput Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBackpropInputTiling结构体的参数说明见下表。 用户通过调用GetTiling接口获取TConv3DBackpropInputTiling结构体，具体流程请参考Conv3DBackpropInput Tiling使用说明。当前暂不支持用户自定义配置TConv3DBackpropInputTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。；- tiling（输出）：Conv3DBackpropInput的Tiling结构体，用于存储最终的Tiling结果。TConv3DBackpropInputTiling结构介绍请参考TConv3DApiTiling结构体说明。。结构体卡定义 Kernel 消费的数据结构，GetTiling 卡定义产生该结构体的 Host 输出，构成明确的生产与消费合同。
<!-- cannbot:related:end -->
