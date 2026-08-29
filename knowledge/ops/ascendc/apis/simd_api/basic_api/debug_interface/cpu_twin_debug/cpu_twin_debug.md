---
type: API
title: CPU孪生调试
description: CPU 孪生调试接口集，包含 GmAlloc、ICPU_RUN_KF、ICPU_SET_TILING_KEY、SetKernelMode 等。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/cpu_twin_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CPU孪生调试

CPU 孪生调试接口集合，用于在 CPU 侧模拟核函数执行以验证逻辑正确性。GmAlloc/GmFree 管理 GM 内存，ICPU_RUN_KF 触发核函数运行，ICPU_SET_TILING_KEY 设置 tiling key，SetKernelMode 设置核运行模式。该方式不依赖真实硬件，适合早期逻辑调试与快速迭代。
