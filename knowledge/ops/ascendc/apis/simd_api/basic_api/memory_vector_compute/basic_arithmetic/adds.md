---
type: API
title: Adds
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量求和。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Adds.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Adds

标量矢量计算接口，每个元素加上标量值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src_i + scalarValue。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Adds](../../reg_vector_compute/basic_arithmetic/adds.md)（`same_topic`）：对srcReg按元素与标量求和，结果写入dstReg；计算公式 dst_i = src_i + scalarValue。两卡实现相同逐元素加标量语义；焦点是 950 RegTensor/VF 形态，候选是 LocalTensor 内存矢量接口并覆盖 950/A2/A3。
- [Adds（灵活标量位置）](adds_flexible_scalar.md)（`same_topic`）：Adds 的灵活标量位置变体，支持标量操作数在 src0 或 src1 位置灵活配置；计算公式 dst_i = src_i + scalarValue。前者是 Adds 对标量位置的 950 扩展，后者给出基础逐元素加标量语义，属于同一计算操作的通用版与变体。
<!-- cannbot:related:end -->
