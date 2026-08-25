---
type: API
title: IcpuRunKf
description: CPU调测总入口，完成CPU侧的算子程序调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/ICPU_RUN_KF.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# IcpuRunKf

CPU 调测总入口，完成 CPU 侧的算子程序调用。通过 ICPU_RUN_KF 宏调用核函数，支持 blockDim、 blockDimI 和 tiling 参数。仅 CPU 调测使用。支持 950/a2/a3。
