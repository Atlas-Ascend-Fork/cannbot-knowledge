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

<!-- cannbot:related:start -->
## 相关

- [内存层级（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步与内存栅栏简介（同步与内存屏障）正文界定“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [同步机制（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；同步与内存栅栏简介（同步与内存屏障）正文说明“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscSyncthreads](sync_interface/asc_syncthreads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《同步与内存栅栏简介（同步与内存屏障）》明确“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [AscThreadfence](memory_fence/asc_threadfence.md)（`related`）：asc_threadfence 把可见性范围扩展到全局内存/其他线程，但仍不是跨 Block barrier；简介中的范围和阻塞差异直接约束其使用。
- [AscThreadfenceBlock](memory_fence/asc_threadfence_block.md)（`related`）：简介把 threadfence_block 定位为不阻塞线程的块内内存顺序与可见性约束，可用于只需发布数据、不需所有线程会合的场景。
- [内存栅栏接口](memory_fence/memory_fence.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《同步与内存栅栏简介（同步与内存屏障）》提供“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
<!-- cannbot:related:end -->
