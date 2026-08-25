---
type: API
title: Mul
description: 双目矢量计算接口，对两个输入tensor按元素求积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mul

双目矢量计算接口，按元素相乘。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src0_i * src1_i。支持 950/a2/a3。
