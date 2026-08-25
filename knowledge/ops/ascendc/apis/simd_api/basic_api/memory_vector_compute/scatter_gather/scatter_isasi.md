---
type: API
title: Scatter
description: 根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Scatter_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Scatter

按索引分散接口，根据索引 tensor 将源 tensor 元素分散写入目的 tensor。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。
