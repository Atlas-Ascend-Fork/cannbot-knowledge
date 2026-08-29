---
type: API
title: Layout数据结构
description: TensorAPI Layout 数据结构集，包含 Layout、Shape、Stride、Coord 及 MakeLayout、GetShape 等相关接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/layout_structure.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Layout数据结构

TensorAPI 中描述张量排布的 Layout 数据结构集合。基础结构含 Layout、Shape、Stride、Coord 及层次化表述法；构造与查询接口含 MakeLayout、MakeFrameLayout、MakeShape、MakeStride、MakeCoord、GetShape、GetStride、Get、Select、Squeeze、Capacity、Size、Coshape、Cosize、Rank。用于解耦张量的逻辑形状与物理排布，属试验特性。
