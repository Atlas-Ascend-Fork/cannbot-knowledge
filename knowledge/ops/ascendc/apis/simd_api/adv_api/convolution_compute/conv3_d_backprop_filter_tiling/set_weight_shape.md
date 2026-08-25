---
type: API
title: SetWeightShape
description: 设置权重矩阵Weight的形状。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.neighborhood.convolution]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/convolution_compute/Conv3DBackpropFilter_Tiling/SetWeightShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# SetWeightShape

设置权重矩阵Weight的形状。

函数原型：void SetWeightShape(int64_t cout, int64_t cin, int64_t d, int64_t h, int64_t w)

参数：
- cout（输入）：设置GradOutput的Channel值。
- cin（输入）：设置Input的Channel值。
- d：输入设置Weight的Depth值。
- h：输入设置Weight的Height值。
- w：输入设置Weight的Width值。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：SetWeightShape 写入的权重维度会被随后调用的 GetTiling 消费，最终生成 TConv3DBpFilterTiling。
- [SetWeightShape](../conv3_d_backprop_input_tiling/set_weight_shape.md)（`related`）：Conv3DBackpropInput 与 BackpropFilter 都暴露同名 SetWeightShape，但前者用 cout/zin 与 GradInput 对齐，后者服务 GradWeight 切分；并列阅读能避免在两套 Tiling 类之间误套参数语义。
- [TConv3DBpFilterTiling结构体](t_conv3_d_bp_filter_tiling_struct.md)（`related`）：TConv3DBpFilterTiling 承载由权重、输入和梯度输出规格计算出的切分结果，是 SetWeightShape 配置在 Kernel 侧生效的下游载体。
- [Conv3DBackpropFilter Tiling侧接口](conv3_d_backprop_filter_tiling.md)（`same_topic`）：Conv3DBackpropFilter Tiling 入口页把 SetWeightShape 列为设置张量形状的核心方法，并说明其结果参与 Host 侧切分。
- [Conv3DBackpropFilterTiling](conv3_d_backprop_filter_tiling_usage.md)（`same_topic`）：Tiling 使用流程要求依次设置 Input、GradOutput、GradWeight 的类型和 Shape 后再调用 GetTiling，SetWeightShape 正是其中的权重形状步骤。
- [SetWeightType](set_weight_type.md)（`same_topic`）：焦点处理Conv3DBackpropFilter Tiling 中 Weight 的位置、格式和数据类型契约；SetWeightShape正文界定“设置权重矩阵Weight的形状”。候选设置同一 Conv3DBackpropFilter Tiling 对象的 Weight 形状/类型，或把该配置传入 GetTiling 与 Kernel SetWeight。
<!-- cannbot:related:end -->
