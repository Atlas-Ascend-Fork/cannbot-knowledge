---
type: API
title: Cast
description: 根据源操作数和目的操作数的数据类型进行精度转换，支持多种舍入模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion/Cast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Cast

类型转换接口，将源 tensor 数据转换为目标数据类型。支持多种舍入模式（ROUND、FLOOR、CEIL、CAST_RINT 等）和数据类型组合。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。
