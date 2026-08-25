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

<!-- cannbot:related:start -->
## 相关

- [内存层级（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；内存栅栏接口正文界定“提供线程与块级别的内存栅栏接口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [内存层级（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`explains`）：内存栅栏为不同 VF/线程观察共享数据提供顺序保证，是混合内存层级中的同步契约。
- [同步机制（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；内存栅栏接口正文说明“提供线程与块级别的内存栅栏接口”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscSyncthreads](../sync_interface/asc_syncthreads.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscSyncthreads》提供“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
- [AscThreadfence](asc_threadfence.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscThreadfence》提供“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
- [AscThreadfenceBlock](asc_threadfence_block.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《AscThreadfenceBlock》提供“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
- [同步与内存栅栏简介（同步与内存屏障）](../sync_and_memory_fence_intro.md)（`same_topic`）：《内存栅栏接口》处理“提供线程与块级别的内存栅栏接口。”。《同步与内存栅栏简介（同步与内存屏障）》提供“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性。”，其具体合同或探针直接接入SIMT fence 的可见性范围、线程同步差异和具体 block/global 接口。
<!-- cannbot:related:end -->
