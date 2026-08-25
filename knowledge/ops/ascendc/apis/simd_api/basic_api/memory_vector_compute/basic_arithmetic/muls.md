---
type: API
title: Muls
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量求积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Muls.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Muls

标量矢量计算接口，每个元素乘以标量值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src_i * scalarValue。支持 950/a2/a3。
