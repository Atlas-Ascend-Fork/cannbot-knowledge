---
type: API
title: AscSyncthreads
description: 阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/sync_and_memory_fence/sync_interface/asc_syncthreads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_syncthreads

在SIMT（Single Instruction Multiple Threads）编程范式中，同一个线程块（Block）内的多个线程并行执行，但各线程的执行进度可能不同。当需要线程间协调工作、共享数据或确保某些操作按顺序执行时，必须使用同步机制。

asc_syncthreads接口用于阻塞当前线程块内所有线程，直到所有线程都执行到该同步点位置。

关键特征：

-   该接口会阻塞线程执行，直到块内所有线程都到达同步点；
-   确保同步点之前的所有内存操作对块内所有线程可见；
-   常用于线程块内的数据共享、分阶段计算、并行归约等场景；

下图展示了同一个线程块内多线程共享数据场景可能出现的问题：

asc_syncthreads接口的执行流程示意图如下：

需要注意，线程块内所有线程必须都调用到asc_syncthreads()接口，程序才能继续执行。如果有线程未到达同步点，其他线程将被阻塞等待，导致死锁，例如：若将本接口的调用放在分支中，就可能导致部分线程到达不了同步接口调用处，导致程序卡死。

函数原型：inline void asc_syncthreads()

返回值：无

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
约束：-   线程块内所有线程必须都执行到同步点，否则会导致死锁。

-   避免分支中调用本接口，除非能确保线程块内所有线程都进入该分支。
-   避免在循环次数不一致的情况下调用。
需包含头文件 "simt_api/device_sync_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
