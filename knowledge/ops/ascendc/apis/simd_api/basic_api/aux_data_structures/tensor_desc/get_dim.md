---
type: API
title: GetDim
description: 获取Tensor的维度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# GetDim

获取TensorDesc指定维度的大小。函数原型：uint32_t GetDim(uint32_t dimIdx) const。参数：dimIdx为维度索引。返回指定维度的大小。用于查询Tensor的各维度大小。
