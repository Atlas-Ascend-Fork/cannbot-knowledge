---
type: API
title: GmAlloc
description: CPU侧运行验证时创建共享内存，在/tmp目录下创建共享文件并返回映射指针。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/GmAlloc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GmAlloc

CPU 侧运行验证时创建共享内存，在 /tmp 目录下创建共享文件并返回映射指针。参数 bufferSize 为申请的内存大小（字节）。仅 CPU 调测使用。支持 950/a2/a3。
