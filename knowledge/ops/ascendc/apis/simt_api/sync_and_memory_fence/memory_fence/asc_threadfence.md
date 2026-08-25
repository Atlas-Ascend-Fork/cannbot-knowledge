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

<!-- cannbot:related:start -->
## 相关

- [同步机制（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；AscThreadfence正文说明“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscSyncthreads](../sync_interface/asc_syncthreads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《AscThreadfence》明确“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [同步与内存栅栏](../sync_and_memory_fence.md)（`related`）：asc_threadfence 只保证全局及共享内存写入的可见顺序且不阻塞线程，是总览中非会合式全局可见性路径。
- [同步与内存栅栏简介（同步与内存屏障）](../sync_and_memory_fence_intro.md)（`related`）：asc_threadfence 把可见性范围扩展到全局内存/其他线程，但仍不是跨 Block barrier；简介中的范围和阻塞差异直接约束其使用。
- [AscThreadfenceBlock](asc_threadfence_block.md)（`same_topic`）：AscThreadfence 提供设备范围内的内存可见性，block 变体只保证线程块范围；二者的选择由消费者作用域决定。
- [内存栅栏接口](memory_fence.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscThreadfence》提供“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
<!-- cannbot:related:end -->
