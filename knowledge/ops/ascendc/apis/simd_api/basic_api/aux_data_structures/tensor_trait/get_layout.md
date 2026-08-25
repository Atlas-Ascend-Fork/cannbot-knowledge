---
type: API
title: GetLayout
description: 获取Layout实例化对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/GetLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# GetLayout

获取TensorTrait的Layout信息。函数原型：Layout GetLayout() const。返回Layout结构体，包含Tensor的排布信息（shape、stride、format等）。用于查询Tensor的数据排布。
