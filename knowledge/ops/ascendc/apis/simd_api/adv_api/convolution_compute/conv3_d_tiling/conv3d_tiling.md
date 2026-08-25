---
type: API
title: Conv3D Tiling侧接口
description: 提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/Conv3d_Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Conv3D Tiling侧接口

提供 Conv3D 前向计算的 Host 侧 Tiling 接口，通过 TConv3DApiTiling 结构体承载切分参数。
核心方法 GetTiling 用于获取最终 Tiling 数据；SetOrgWeightShape/SetOrgInputShape 设置原始权重与输入形状，SetSingleWeightShape/SetSingleOutputShape 设置单次计算形状。
另提供 SetInputType/SetWeightType/SetBiasType/SetOutputType 设置数据类型，SetPadding/SetDilation/SetStride/SetGroups 设置卷积超参数。
