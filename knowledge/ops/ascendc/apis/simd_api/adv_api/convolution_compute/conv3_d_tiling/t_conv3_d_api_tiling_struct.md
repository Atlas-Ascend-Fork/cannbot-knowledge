---
type: API
title: TConv3DApiTiling结构体
description: TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/TConv3DApiTiling_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# TConv3DApiTiling结构体

TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。TConv3DApiTiling结构体的参数说明见表1。 用户通过调用GetTiling接口获取TConv3DApiTiling结构体，具体流程请参考Conv3D Tiling使用说明。当前暂不支持用户自定义配置TConv3DApiTiling结构体中的参数。

<!-- cannbot:related:start -->
## 相关

- [Conv3D Tiling使用说明](conv3_d_tiling_usage.md)（`related`）：结构体卡指出“用户通过调用GetTiling接口获取TConv3DApiTiling结构体，具体流程请参考Conv3D Tiling使用说明。”；使用说明给出“调用API接口，即可获取Init中TConv3DApiTiling结构体中的相关参数。”，把结构体字段接到对象创建、参数设置、GetTiling 和 Kernel Init 的完整调用顺序。
- [GetTiling](get_tiling.md)（`related`）：结构体卡说明“TConv3DApiTiling结构体包含Conv3D算子规格信息及Tiling切分算法的相关参数，被传递给Conv3D Kernel侧，用于数据切分、数据搬运和计算等。”；GetTiling 卡规定“tiling（输出）：Conv3D的Tiling结构体，用于存储最终的Tiling结果。”，明确了该结构体的 Host 生产接口。
<!-- cannbot:related:end -->
