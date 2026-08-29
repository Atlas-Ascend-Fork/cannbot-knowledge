---
type: API
title: ViewEngine
description: ViewEngine是Tensor API中的视图引擎，负责持有一个指针对象Iterator，通过Begin()返回这段视图的起始位置。在LocalTensor中，ViewEngine和Layout一起组成一个Tensor的视图。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/ViewEngine.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# ViewEngine

Tensor API 中的视图引擎，持有指针对象 Iterator，通过 Begin() 返回视图起始位置。在 LocalTensor 中，ViewEngine 与 Layout 组成 Tensor 的视图。头文件 `tensor_api/tensor.h`。仅 950 支持。
