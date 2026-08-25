---
type: API
title: Pointer（基础API）
description: Pointer定义指针迭代器，用于遍历和访问张量数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/Pointer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Pointer（基础API）

Pointer定义指针迭代器，用于遍历和访问张量数据。

# Pointer（基础API）

Pointer定义指针迭代器，用于遍历和访问张量数据。

本接口属于 Tensor 数据结构操作接口，用于描述和操作张量的布局与结构。

参数说明：ptr：T* 指向数据的指针。；position：P 指针的位置信息。

约束：ptr指针必须指向有效的内存空间。；position必须正确描述指针的当前位置。；Pointer支持多种内存空间的指针类型。

本接口为 Ascend C 算子开发 API，具体使用方法和约束请参考官方文档。
