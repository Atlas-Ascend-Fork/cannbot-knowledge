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
