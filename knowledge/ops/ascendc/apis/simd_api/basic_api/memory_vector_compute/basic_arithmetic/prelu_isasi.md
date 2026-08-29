---
type: API
title: Prelu
description: 双目矢量计算接口，src0非负时直接输出，否则输出src0与src1的乘积。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Prelu_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Prelu

单目矢量计算接口，按元素计算 PReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(0, src_i) + alpha * min(0, src_i)。仅 950 支持。
