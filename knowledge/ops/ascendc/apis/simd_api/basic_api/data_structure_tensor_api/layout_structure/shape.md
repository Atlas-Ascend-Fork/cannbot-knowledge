---
type: API
title: Shape（基础API）
description: 定义张量各维度的逻辑大小，并与 Stride 组合形成支持层次化表述的 Layout。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Shape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Shape（基础API）

Shape 用于定义数据的逻辑形状，如矩阵的行数和列数或多维张量各维度大小。与 Stride 配合构成 Layout，支持层次化表述（元素可为元组）。通过 MakeShape 构造。头文件 `tensor_api/tensor.h`。

<!-- cannbot:related:start -->
## 相关

- [Coshape](coshape.md)（`related`）：CoShape 表示与 shape 对偶的坐标/余形结构，适合布局变换而非替代普通 Shape。
- [MakeLayout](make_layout.md)（`related`）：MakeLayout 消费 Shape 与 Stride 构造寻址布局，是 Shape 的直接下游。
- [MakeShape](../../aux_data_structures/layout/make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《Shape（基础API）》说明定义张量各维度的逻辑大小，并与 Stride 组合形成支持层次化表述的 Layout。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [GetShape](get_shape.md)（`same_topic`）：GetShape 从 Layout 读取 Shape，连接布局对象与 shape 查询。
- [MakeShape](make_shape.md)（`same_topic`）：MakeShape 构造 Shape 对象，是类型页所描述 shape 的主要创建入口。
- [基础APIRank](rank.md)（`same_topic`）：基础APIRank 与《Shape（基础API）》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《Shape（基础API）》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
