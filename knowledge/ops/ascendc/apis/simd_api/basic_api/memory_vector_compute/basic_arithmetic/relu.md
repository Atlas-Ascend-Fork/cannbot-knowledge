---
type: API
title: Relu
description: 单目矢量计算接口，对输入tensor按元素做ReLU计算，负值置零，非负值原样输出。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Relu

单目矢量计算接口，按元素计算 ReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(0, src_i)。支持 950/a2/a3。
