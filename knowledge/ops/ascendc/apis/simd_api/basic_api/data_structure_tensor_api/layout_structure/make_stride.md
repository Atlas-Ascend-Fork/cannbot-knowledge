---
type: API
title: MakeStride
description: 构造Stride对象，用于描述各维度在内存中的步长。支持传入多个步长值，也支持传入嵌套的Stride子结构以构造层次化Stride。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/MakeStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MakeStride

构造 Stride 对象描述各维度内存步长。支持传入多个步长值，也支持嵌套 Stride 子结构构造层次化 Stride。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [MakeLayout](make_layout.md)（`related`）：MakeLayout 消费 MakeShape 与 MakeStride 的结果形成可寻址布局，是 MakeStride 的直接下游。
- [MakePatternLayout](make_pattern_layout.md)（`related`）：MakePatternLayout 与《MakeStride》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [MakeShape](make_shape.md)（`related`）：Shape 描述逻辑维度、Stride 描述各维内存步长，二者是 MakeLayout 的两个互补输入。
- [GetStride](get_stride.md)（`same_topic`）：MakeStride说明构造Stride对象，用于描述各维度在内存中的步长。支持传入多个步长值，也支持传入嵌套的Stride子结构以构造层次化Stride。
- [Stride（基础API）](stride.md)（`same_topic`）：Stride 类型是 MakeStride 构造的返回对象，定义各维地址步长的静态表示。
<!-- cannbot:related:end -->
