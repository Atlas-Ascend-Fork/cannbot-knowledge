---
type: API
title: Adds（灵活标量位置）
description: 矢量元素与标量做加法，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Adds_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Adds（灵活标量位置）

Adds 的灵活标量位置变体，支持标量操作数在 src0 或 src1 位置灵活配置。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Adds](adds.md)（`same_topic`）：Adds 的灵活标量位置变体，支持标量操作数在 src0 或 src1 位置灵活配置；计算公式 dst_i = src_i + scalarValue。前者是 Adds 对标量位置的 950 扩展，后者给出基础逐元素加标量语义，属于同一计算操作的通用版与变体。
<!-- cannbot:related:end -->
