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

<!-- cannbot:related:start -->
## 相关

- [内存层级（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步与内存栅栏正文界定“同步与内存栅栏接口索引，包含同步接口与内存栅栏接口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [同步机制（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/synchronization.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；同步与内存栅栏正文说明“同步与内存栅栏接口索引，包含同步接口与内存栅栏接口”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscThreadfence](memory_fence/asc_threadfence.md)（`related`）：asc_threadfence 只保证全局及共享内存写入的可见顺序且不阻塞线程，是总览中非会合式全局可见性路径。
- [AscThreadfenceBlock](memory_fence/asc_threadfence_block.md)（`related`）：asc_threadfence_block 把可见性限制在同一 Block，适用于无需全局屏障的低范围生产者—消费者关系。
- [同步控制](../../simd_api/c_api/sync/sync_control.md)（`related`）：同步控制 与《同步与内存栅栏》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
<!-- cannbot:related:end -->
