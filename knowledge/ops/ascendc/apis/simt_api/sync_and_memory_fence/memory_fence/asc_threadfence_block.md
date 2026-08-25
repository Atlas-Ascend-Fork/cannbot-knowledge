---
type: API
title: AscThreadfenceBlock
description: Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/memory_fence/asc_threadfence_block.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_threadfence_block

Block 范围内存栅栏函数。保证当前线程在调用 asc_threadfence_block() 之前的所有内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束 Block 范围可见性顺序。相比 asc_threadfence 仅需保证 Block 内共享缓存层级一致性，无需全局内存屏障。

函数原型：inline void asc_threadfence_block()

无参数，无返回值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_sync_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
