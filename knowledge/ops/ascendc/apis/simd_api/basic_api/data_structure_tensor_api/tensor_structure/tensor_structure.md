---
type: API
title: Tensor数据结构
description: TensorAPI Tensor 数据结构集，包含 Tensor、Pointer、ViewEngine 及 MakeTensor、Slice 等相关接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/tensor_structure.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Tensor数据结构

TensorAPI 中描述张量对象的 Tensor 数据结构集合。包含 Tensor、Pointer、ViewEngine 三类基础结构，以及 MakeTensor、MakeMemPtr、Slice 等构造与切片接口。Tensor 与 Layout 配合使用，提供对缓冲区数据的视图化访问能力，属试验特性。
