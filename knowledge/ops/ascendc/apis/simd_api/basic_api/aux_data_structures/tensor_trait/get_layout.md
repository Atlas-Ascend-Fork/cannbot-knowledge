---
type: API
title: GetLayout
description: 获取Layout实例化对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/GetLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetLayout

获取TensorTrait的Layout信息。函数原型：Layout GetLayout() const。返回Layout结构体，包含Tensor的排布信息（shape、stride、format等）。用于查询Tensor的数据排布。

<!-- cannbot:related:start -->
## 相关

- [MakeTensorTrait](make_tensor_trait.md)（`related`）：MakeTensorTrait 从 Layout 生成 TensorTrait 实例，随后可通过 GetLayout 取回布局，连接构造与查询阶段。
- [TensorTrait构造函数](tensor_trait_constructor.md)（`related`）：构造时写入的 Layout 正是 GetLayout 返回的排布信息，形成创建 TensorTrait 后验证/消费 layout 的直接链路。
- [SetLayout](set_layout.md)（`same_topic`）：SetLayout 写入 TensorTrait 的 Layout，GetLayout 读取同一对象，形成直接写后查询契约。
- [TensorTrait](tensor_trait.md)（`same_topic`）：TensorTrait 与《GetLayout》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [TensorTrait简介](tensor_trait_intro.md)（`same_topic`）：GetLayout 读取 TensorTrait 携带的布局，使后续 Tensor API 能消费该编译期描述。
- [layout](../layout/layout1.md)（`same_topic`）：layout 与《GetLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
<!-- cannbot:related:end -->
