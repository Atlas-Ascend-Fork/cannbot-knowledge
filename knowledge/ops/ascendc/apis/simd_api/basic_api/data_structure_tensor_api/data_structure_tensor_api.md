---
type: API
title: 数据结构(TensorAPI，试验特性)
description: TensorAPI（试验特性）数据结构总览，涵盖内置数据类型、Layout 与 Tensor 相关数据结构及工具接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/data_structure_TensorAPI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数据结构(TensorAPI，试验特性)

TensorAPI（试验特性）数据结构总览，提供基于 Layout 与 Tensor 抽象的层次化张量编程模型。包含内置数据类型与精度转换；Layout 侧提供 Layout、Shape、Stride、Coord 及构造/查询接口（MakeLayout、GetShape 等）；Tensor 侧提供 Tensor、Pointer、ViewEngine 及 MakeTensor、Slice 等接口；GetLayoutPattern 为工具接口。属试验特性，接口可能随版本调整。
