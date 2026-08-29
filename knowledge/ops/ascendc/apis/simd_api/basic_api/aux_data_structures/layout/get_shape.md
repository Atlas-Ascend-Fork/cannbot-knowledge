---
type: API
title: GetShape
description: 返回描述张量形状的Shape对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/GetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# GetShape

获取Layout的Shape信息。返回Layout中描述的各维度大小。函数原型：Shape GetShape() const。返回Shape结构体，包含各维度大小。用于查询Tensor的形状信息。
