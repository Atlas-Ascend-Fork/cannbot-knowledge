---
type: API
title: LeakyRelu
description: 矢量元素执行Leaky ReLU操作：非负值原样输出，负值乘以标量系数后输出。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/LeakyRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LeakyRelu

单目矢量计算接口，按元素计算 LeakyReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(src_i, alpha*src_i)，alpha 为斜率系数。支持 950/a2/a3。
