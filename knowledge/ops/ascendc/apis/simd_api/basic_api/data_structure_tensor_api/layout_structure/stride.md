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
