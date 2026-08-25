---
type: API
title: Maxs
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量取最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Maxs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Maxs

标量矢量计算接口，每个元素与标量取最大值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = max(src_i, scalarValue)。支持 950/a2/a3。
