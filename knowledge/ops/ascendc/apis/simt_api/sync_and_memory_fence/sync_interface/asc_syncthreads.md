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

<!-- cannbot:related:start -->
## 相关

- [同步机制（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《同步机制（AI Core SIMT编程）》明确“SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [AscThreadfence](../memory_fence/asc_threadfence.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《AscThreadfence》明确“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [AscThreadfenceBlock](../memory_fence/asc_threadfence_block.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《AscThreadfenceBlock》明确“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [NumThreads](../../cooperative_groups/thread_block/num_threads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《NumThreads》明确“获取当前线程所属线程块内的线程总数。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [ThreadBlock协作组size](../../cooperative_groups/thread_block/size.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《ThreadBlock协作组size》明确“获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [同步与内存栅栏简介（同步与内存屏障）](../sync_and_memory_fence_intro.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《同步与内存栅栏简介（同步与内存屏障）》明确“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [内存栅栏接口](../memory_fence/memory_fence.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscSyncthreads》提供“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
- [同步接口](sync_interface.md)（`same_topic`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《同步接口》明确“提供块内线程同步接口。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
<!-- cannbot:related:end -->
