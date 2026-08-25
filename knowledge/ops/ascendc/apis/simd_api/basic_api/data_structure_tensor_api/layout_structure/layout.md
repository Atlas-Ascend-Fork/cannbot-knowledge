---
type: API
title: Layout
description: Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Layout

试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。

核心方法：Shape()/Stride() 获取形状/步长，Capacity() 内存容量，Size() 有效元素数，Rank() 秩，Get/Select 提取子 Layout，Squeeze 删除 size=1 维度，Coshape/Cosize 陪域大小。支持层次化表述法（元素可为元组）描述 NZ/Zz/Zn 等分形格式。试验接口，不保证后续兼容性。
