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
