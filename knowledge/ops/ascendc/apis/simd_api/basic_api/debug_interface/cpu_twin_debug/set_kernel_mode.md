---
type: API
title: SetKernelMode
description: CPU调测时设置内核模式为AIV、AIC或MIX模式，分别支持矢量、矩阵和混合算子调试。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/SetKernelMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetKernelMode

CPU 调测时设置内核模式：AIV（矢量算子）、AIC（矩阵算子）或 MIX（混合模式）。参数 mode 为 KernelMode 枚举。仅 CPU 调测使用。支持 950/a2/a3。
