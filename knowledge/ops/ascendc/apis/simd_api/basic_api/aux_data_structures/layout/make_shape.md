---
type: API
title: MakeShape
description: 将传入的数据打包成Shape数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/MakeShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# MakeShape

构造Shape结构体的辅助函数。通过传入各维度大小创建Shape。函数原型提供1维到8维的构造重载。参数为各维度的size值。返回Shape结构体。用于快速创建Tensor形状描述。
