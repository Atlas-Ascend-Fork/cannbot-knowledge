---
type: API
title: SetOrgWeightShape
description: 设置权重矩阵Weight的原始形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3D_Tiling/SetOrgWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetOrgWeightShape

设置权重矩阵Weight的原始形状。

函数原型：void SetOrgWeightShape(int64_t orgCo, int64_t orgKd, int64_t orgKh, int64_t orgKw)

参数：
- orgCo（输入）：原始输出通道的大小。
- orgKd（输入）：原始Weight D维度大小。
- orgKh（输入）：原始Weight H维度大小。
- orgKw（输入）：原始Weight W维度大小。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：《GetTiling》明确“获取Tiling参数。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetSingleWeightShape](set_single_weight_shape.md)（`related`）：《SetSingleWeightShape》明确“设置单核上权重矩阵Weight的形状。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetWeightType](set_weight_type.md)（`related`）：权重类型与原始 Co/Kd/Kh/Kw 形状共同构成 Conv3D tiling 对 Weight 的完整描述，缺一不能可靠生成切分参数。
- [Conv3D Tiling侧接口](conv3d_tiling.md)（`same_topic`）：《Conv3D Tiling侧接口》明确“提供Conv3D前向计算的Host侧Tiling接口，包含TConv3DApiTiling结构体、GetTiling及形状与类型设置方法。”；它与《SetOrgWeightShape》的“设置权重矩阵Weight的原始形状。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
