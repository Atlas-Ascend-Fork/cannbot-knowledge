---
type: API
title: Compares
description: 逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compares.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Compares

逐元素比较 tensor 与标量值大小，结果为真则对应比特位为 1。支持 EQ、NE、GT、GE、LT、LE 等比较模式。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。
