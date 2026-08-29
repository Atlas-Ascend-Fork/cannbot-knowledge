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

- [Stride（基础API）](stride.md)（`related`）：Stride 用于定义各维度在内存中的步长，即同维度相邻元素在内存中的间隔，单位为元素，与 Shape 维度一一对应。；构造 Stride 对象描述各维度内存步长。。前者定义 Stride 对象表达的逐维元素间隔及其与 Shape 的对应关系，后者是构造该对象的入口，二者形成布局步长语义到对象创建的直接使用链。
<!-- cannbot:related:end -->
