---
type: API
title: SetSingleOutputShape
description: 设置单核上结果矩阵Output的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetSingleOutputShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetSingleOutputShape

设置单核上结果矩阵Output的形状。

函数原型：void SetSingleOutputShape(int64_t singleCo, int64_t singleDo, int64_t singleM)

参数：
- singleCo（输入）：单核上输出通道的大小。
- singleDo（输入）：单核上Output D维度大小。
- singleM（输入）：单核上Output M维度大小。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetSingleOutputShape](../conv3_d_kernel/set_single_output_shape.md)（`same_topic`）：《SetSingleOutputShape》明确“设置单核上结果矩阵Output的形状。 Conv3D高阶API目前支持M合轴模式的输出方式。在M合轴模式下，Conv3D API内部将Wout和Hout视为同一轴处理，输出时先沿Wout方向输出，完成一整行Wout输出后，再进行下一行的Wout输出。 图1 M合轴模式示意图”；它与《SetSingleOutputShape》的“设置单核上结果矩阵Output的形状。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
