---
type: Guide
title: 原子操作（AI Core SIMT编程）
description: SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global
  Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能出现数据竞争，导致最终结果不符合预期。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 原子操作

SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能出现数据竞争，导致最终结果不符合预期。

原子操作用于保证同一地址上的一次读-改-写过程不可被其他线程打断。典型场景包括计数、状态抢占、直方图统计和并行归约等。

## 基本语义

原子操作保证的是单次内存更新的原子性。例如多个线程同时对同一个计数器执行`asc_atomic_add`时，每次加法都会以原子方式完成，不会出现多个线程读取同一个旧值后覆盖彼此结果的问题。

原子操作不保证多个线程到达该原子操作的先后顺序，也不是线程同步屏障。多个Thread、Warp或Thread Block同时访问同一地址时，硬件会对这些原子请求进行串行化处理，但串行化顺序通常不由程序指定。

Ascend C SIMT提供`asc_atomic_add`、`asc_atomic_sub`、`asc_atomic_cas`等原子操作接口，可用于Global Memory或Unified Buffer中的数据更新。不同接口支持的数据类型、访问空间和返回值约束不同，详细说明请参见原子操作接口。

## 使用建议

- 仅在确实存在并发写同一地址且需要保证更新不丢失时使用原子操作。
- 不要将原子操作等同于线程同步；需要线程到达同一执行点时，应使用同步接口。
- 避免大量线程频繁原子更新同一个Global Memory地址，必要时先在Thread Block内做局部聚合。
- 不要依赖原子操作返回值表达稳定的线程执行顺序。

<!-- cannbot:related:start -->
## 相关

- [AscAtomicCas](../../../../apis/simd_api/c_api/scalar_compute/asc_atomic_cas.md)（`explains`）：原子操作（AI Core SIMT编程）说明SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能出现数据竞争，导致最终结果不符合预期。
- [AtomicCas](../../../../apis/simd_api/basic_api/atomic_operations/atomic_cas.md)（`explains`）：该指南解释并发读改写的数据竞争以及必须使用原子的场景，为 AtomicCas 何时用于状态抢占和条件更新提供使用边界。
- [原子操作](../../../../apis/simt_api/atomic_operations/atomic_operations.md)（`explains`）：原子操作 与《原子操作（AI Core SIMT编程）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作简介](../../../../apis/simt_api/atomic_operations/atomic_operations_intro.md)（`explains`）：指南解释 SIMT 线程并发访问 GM/UB 时为何需要原子读改写，并给出数据竞争语境。
- [原子操作边界值汇总（附录）](../../../../apis/appendix/atomic_operations_interface_boundary_value_summary.md)（`explains`）：焦点处理原子操作在边界输入下的结果解释；原子操作（AI Core SIMT编程）正文说明“SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
- [AiCoreSimtProgrammingOverview](overview.md)（`related`）：SIMT 总览提供 Grid-Block-Thread 并发和 Warp 调度背景，定位原子操作所解决的数据竞争来源。
- [ThreadArchitecture](thread_architecture.md)（`related`）：Thread/Block/Grid 的独立执行与共享范围决定哪些线程可能并发更新同一地址，是选择原子作用域的前提。
- [内存层级（AI Core SIMT编程）](memory_hierarchy.md)（`related`）：原子接口可作用于 Global Memory 或 Unified Buffer；内存层级卡给出两者的线程作用域和生命周期，决定竞争范围。
- [同步机制（AI Core SIMT编程）](synchronization.md)（`related`）：同步指南明确 barrier/fence 不能替代并发同址读改写的原子操作，并说明跨 Thread Block 需组合 Global Memory、原子与 fence。
<!-- cannbot:related:end -->
