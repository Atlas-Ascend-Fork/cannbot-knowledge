---
type: API
title: Stride（基础API）
description: 定义张量各维度相邻元素的内存步长，并与 Shape 组合形成 Layout。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Stride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Stride（基础API）

Stride 用于定义各维度在内存中的步长，即同维度相邻元素在内存中的间隔，单位为元素，与 Shape 维度一一对应。与 Shape 配合构成 Layout，支持层次化表述。通过 MakeStride 构造。头文件 `tensor_api/tensor.h`。

<!-- cannbot:related:start -->
## 相关

- [Capacity（基础API）](capacity.md)（`related`）：Capacity 由 shape/stride 共同决定物理覆盖范围，可用于验证自定义 Stride 是否导致越界或空洞。
- [MakeLayout](make_layout.md)（`related`）：MakeLayout 消费 Shape 与 Stride 形成寻址映射，是 Stride 的直接下游。
- [GetStride](get_stride.md)（`same_topic`）：Stride（基础API）说明定义张量各维度相邻元素的内存步长，并与 Shape 组合形成 Layout。
- [MakeStride](make_stride.md)（`same_topic`）：Stride 类型是 MakeStride 构造的返回对象，定义各维地址步长的静态表示。
- [基础APIRank](rank.md)（`same_topic`）：基础APIRank 与《Stride（基础API）》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《Stride（基础API）》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
