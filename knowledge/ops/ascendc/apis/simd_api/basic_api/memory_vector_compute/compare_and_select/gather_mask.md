---
type: API
title: GatherMask
description: 以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GatherMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GatherMask

根据 mask 从源 tensor 中收集有效元素到目的 tensor。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。
