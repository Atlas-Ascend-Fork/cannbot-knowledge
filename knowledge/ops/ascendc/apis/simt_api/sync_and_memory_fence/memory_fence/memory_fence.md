---
type: API
title: 内存栅栏接口
description: 提供线程与块级别的内存栅栏接口。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/memory_fence/memory_fence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 内存栅栏接口

SIMT API内存栅栏接口集合，用于多线程编程中的内存可见性控制。包含asc_threadfence（线程级内存栅栏，保证当前线程在栅栏之前的所有内存写操作对设备上所有线程可见，确保数据一致性）和asc_threadfence_block（块级内存栅栏，保证当前线程块在栅栏之前的所有内存写操作对设备上所有线程块可见）。在SIMT并行计算中，合理使用内存栅栏可避免数据竞争和可见性问题。
