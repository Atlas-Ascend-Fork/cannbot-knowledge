---
type: API
title: Layout和层次化表述法
description: Layout通过Shape和Stride表示张量排布格式，层次化表述法支持元组嵌套描述复杂内存排布如分形格式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Layout_hierarchical_representation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Layout和层次化表述法

Layout 用 Shape 和 Stride 表示张量排布：行优先 Shape(2,4) Stride(4,1)，列优先 Shape(2,4) Stride(1,2)。层次化表述法允许 Shape/Stride 元素为元组，描述内外层嵌套矩阵，如 Shape((2,3),(2,4)) Stride((1,4),(2,12))。

Ascend C 矩阵编程常用分形 Layout 采用两层嵌套：Shape((内层行,外层行),(内层列,外层列))，Stride 对应。常见分形含 NZ（大N小z）、Zz（大Z小z）、Zn（大Z小n）、Nd、Dn 等，通过 LayoutPattern 和 LayoutTrait 描述。

<!-- cannbot:related:start -->
## 相关

- [MakeLayout](make_layout.md)（`related`）：层次化表述最终仍由嵌套 Shape 与 Stride 构造 Layout；MakeLayout 是把该表述落成可索引对象的基础入口。
- [MakePatternLayout](make_pattern_layout.md)（`related`）：MakePatternLayout 与《Layout和层次化表述法》的衔接是：MakePatternLayout 把 LayoutPattern/Trait 附着到由 Shape、Stride 构成的 Layout；GetLayoutPattern 和 MakeLayout 是读取与构造同一元数据的配套步骤，方向不匹配会造成矩阵布局解释错误。
- [Coord（基础API）](coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Layout和层次化表述法正文说明“Layout通过Shape和Stride表示张量排布格式，层次化表述法支持元组嵌套描述复杂内存排布如分形格式”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout](layout.md)（`same_topic`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《Layout和层次化表述法》补充：Layout通过Shape和Stride表示张量排布格式，层次化表述法支持元组嵌套描述复杂内存排布如分形格式。
- [基础APIRank](rank.md)（`same_topic`）：基础APIRank 与《Layout和层次化表述法》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《Layout和层次化表述法》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
