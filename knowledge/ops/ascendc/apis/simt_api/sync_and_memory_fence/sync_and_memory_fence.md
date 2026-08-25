---
type: API
title: 同步与内存栅栏
description: 同步与内存栅栏接口索引，包含同步接口与内存栅栏接口。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/sync_and_memory_fence.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步与内存栅栏

SIMT 程序中不同 Thread 的执行进度和内存访问到达顺序可能不同，存在数据依赖时需要通过同步或内存栅栏接口约束执行顺序与可见性。同步机制分两类：同步屏障（barrier）阻塞当前 Thread Block 内所有 Thread 直到全部到达同步点；内存栅栏（memory fence）仅约束调用线程在栅栏前后的内存访问顺序，不阻塞其他线程。
本入口包含三部分导航：同步与内存栅栏简介说明使用场景与选型建议；同步接口提供 Thread Block 内的阶段同步能力；内存栅栏接口提供块内或全局范围的内存可见性顺序约束。
注意：asc_syncthreads 不能用于跨 Thread Block 同步；内存栅栏不能替代同步屏障；多线程并发写同一地址仍需使用原子操作。
