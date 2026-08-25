---
type: API
title: Select
description: 根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Select

根据 mask 从两个源 tensor 中选择元素，mask 为 1 选 src0，为 0 选 src1。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。
