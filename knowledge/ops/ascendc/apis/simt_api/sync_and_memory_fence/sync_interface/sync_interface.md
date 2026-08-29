---
type: API
title: 同步接口
description: 提供块内线程同步接口。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/sync_interface/sync_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 同步接口

同步接口用于 SIMT 编程中 Thread Block 内的阶段同步，当前提供 asc_syncthreads。该接口阻塞当前 Thread Block 内所有 Thread，直到全部到达同步点，并保证同步点前的内存操作对块内所有 Thread 可见，常用于块内数据共享、分阶段计算和并行归约场景。
约束：Thread Block 内所有 Thread 必须都执行到同步点，否则会导致死锁；避免在分支或循环次数不一致的情况下调用，除非能确保块内所有 Thread 都进入该分支。
asc_syncthreads 仅同步当前 Thread Block，不能用于跨 Thread Block 的全局同步。
