---
type: API
title: 同步与内存栅栏简介（同步与内存屏障）
description: SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/sync_and_memory_fence_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步与内存栅栏简介

SIMT 程序中不同 Thread 的执行进度和内存访问到达顺序可能不同，线程间存在数据依赖时需使用同步或内存栅栏接口约束执行顺序和内存可见性。

同步机制分两类：同步屏障（barrier）要求作用范围内所有线程到达指定位置后继续；内存栅栏（memory fence）约束调用线程栅栏前后的内存访问顺序，使栅栏前内存操作按指定范围对其他线程可见，不阻塞其他线程。

API 列表：asc_syncthreads（Thread Block 范围同步屏障，阻塞线程，等待块内所有线程到达同步点并保证内存操作对块内可见）；asc_threadfence_block（Thread Block 范围内存栅栏，不阻塞，保证块内可见性顺序）；asc_threadfence（全局范围内存栅栏，不阻塞，保证全局内存和共享内存写操作对其他线程可见）。

使用建议：块内阶段同步用 asc_syncthreads；仅需保证内存写入顺序和可见性用 asc_threadfence 或 asc_threadfence_block；内存栅栏不等价于同步屏障，不等待其他线程；asc_syncthreads 不能用于跨 Block 同步；并发写同一地址时同步和栅栏均不能替代原子操作。
