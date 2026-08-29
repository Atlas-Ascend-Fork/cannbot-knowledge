---
type: API
title: 基础APIGet
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素；
  2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Get.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 基础APIGet

提供两类能力：对 Tuple 按位置索引提取元素或逐层提取嵌套元素；对 Layout 分别从 Shape 和 Stride 中提取对应位置的子 tuple 组合为新的子 Layout。头文件 `tensor_api/tensor.h`。仅 950 支持。
