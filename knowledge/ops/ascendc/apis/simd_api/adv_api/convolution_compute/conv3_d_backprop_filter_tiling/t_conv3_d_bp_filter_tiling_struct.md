---
type: API
title: TConv3DBpFilterTiling结构体
description: TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter
  Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/TConv3DBpFilterTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# TConv3DBpFilterTiling结构体

TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DBpFilterTiling结构体，具体流程请参考使用说明。当前暂不支持用户自定义配置TConv3DBpFilterTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：“- tiling（输出）：TConv3DBpFilterTiling的Tiling结构体，用于存储最终的Tiling结果。TConv3DBpFilterTiling结构介绍请参考TConv3DBpFilterTiling结构体。”与“TConv3DBpFilterTiling结构体包含Conv3dBackpropFilter算子规格信息及Tiling切分算法的相关参数，被传递给Conv3dBackpropFilter Kernel侧，用于数据切分、数据搬运和计算等。TConv3DBpFilterTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DBpFilterTiling结构体，具体流程请参考使用说明。当前暂不支持用户自定义配置TConv3DBpFilterTiling结构体中的参数。 具体字段、含义和取值约束见固定来源中的结构说明表。”。GetTiling 的输出正是结构体卡定义的 Kernel 切分、搬运与计算参数载体。
<!-- cannbot:related:end -->
