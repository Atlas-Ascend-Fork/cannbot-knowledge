---
type: API
title: Select（基础API）
description: 选择Layout的shape和stride指定维度组成新的layout对象并返回。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Select（基础API）

选择 Layout 的 Shape 和 Stride 中指定维度，组成新的子 Layout 对象返回。头文件为 tensor_api/tensor.h。
通过模板参数 Is 指定要保留的维度索引序列，编译时递归选择 shape 和 stride 的子结构。
函数签名为 template <size_t... Is, typename Shape, typename Stride> auto Select(const Layout<Shape, Stride>& layout)，返回子 Layout 对象。
约束：索引 Is 必须在有效维度范围内，否则编译失败。
典型用法：对三维 Layout 调用 Select<0, 1> 可得到由第 0、1 维组成的新 Layout。本接口为试验接口，仅 Ascend 950PR/950DT 支持。
