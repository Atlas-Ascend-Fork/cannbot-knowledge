---
type: API
title: AscThreadfence
description: 内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/memory_fence/asc_threadfence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_threadfence

全局内存栅栏函数。保证调用线程在 asc_threadfence() 之前的所有全局内存和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。适用于生产者-消费者同步、原子计数器、指针更新和多线程共享数据等场景。

函数原型：inline void asc_threadfence()

无参数，无返回值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_sync_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。典型用法：生产者写入数据后调用 asc_threadfence() 确保写入顺序可见，再设置标志位；消费者轮询标志位后读取数据。
