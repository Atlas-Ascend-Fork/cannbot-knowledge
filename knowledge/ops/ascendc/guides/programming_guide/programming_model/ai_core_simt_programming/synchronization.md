---
type: Guide
title: 同步机制（AI Core SIMT编程）
description: SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread
  Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/synchronization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 同步机制

SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：
- 同步屏障（barrier）：要求同一作用范围内的线程都到达指定位置后，程序才能继续执行。
- 内存栅栏（memory fence）：约束调用线程在栅栏前后的内存访问顺序，使栅栏前的内存操作按指定范围对其他线程可见。内存栅栏不会等待其他线程到达同一位置。
## 接口概览
同步屏障：asc_syncthreads：Thread Block内阶段同步，例如先写Unified Buffer，再统一读取。
内存栅栏：asc_threadfence_block、asc_threadfence：发布数据或标志前，约束当前Thread的内存访问顺序和可见性。
同步接口和内存栅栏接口的详细语义、作用范围、使用示例及注意事项，请参见同步与内存栅栏简介。
## 使用建议
- 需要Thread Block内所有Thread完成某一阶段后再继续执行时，使用同步屏障。
- 只需要保证当前Thread的内存写入顺序和可见性时，使用内存栅栏。
- 不要将内存栅栏当作同步屏障使用。内存栅栏不会等待其他Thread，也不保证其他Thread已经执行到同一位置。
- 不要将同步屏障当作跨Thread Block同步接口使用。不同Thread Block之间如需共享状态，应结合Global Memory、原子操作和内存栅栏设计同步协议。
- 多个Thread并发写同一地址时，同步屏障和内存栅栏都不能替代原子操作；需要避免写冲突，可使用原子操作保证读改写过程的原子性。

<!-- cannbot:related:start -->
## 相关

- [AscSyncthreads](../../../../apis/simt_api/sync_and_memory_fence/sync_interface/asc_syncthreads.md)（`explains`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《同步机制（AI Core SIMT编程）》明确“SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [AscThreadfence](../../../../apis/simt_api/sync_and_memory_fence/memory_fence/asc_threadfence.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；AscThreadfence正文说明“内存栅栏接口，保证调用前的全局和共享内存写操作对其他线程可见，不阻塞线程，仅约束可见性顺序”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [AscThreadfenceBlock](../../../../apis/simt_api/sync_and_memory_fence/memory_fence/asc_threadfence_block.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；AscThreadfenceBlock正文说明“Block范围内存栅栏接口，保证调用前的内存读写操作对同一线程块内其他线程可见，不阻塞线程，仅约束Block范围可见性”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [内存栅栏接口](../../../../apis/simt_api/sync_and_memory_fence/memory_fence/memory_fence.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；内存栅栏接口正文说明“提供线程与块级别的内存栅栏接口”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [同步与内存栅栏](../../../../apis/simt_api/sync_and_memory_fence/sync_and_memory_fence.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；同步与内存栅栏正文说明“同步与内存栅栏接口索引，包含同步接口与内存栅栏接口”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [同步与内存栅栏简介（同步与内存屏障）](../../../../apis/simt_api/sync_and_memory_fence/sync_and_memory_fence_intro.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；同步与内存栅栏简介（同步与内存屏障）正文说明“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [同步接口](../../../../apis/simt_api/sync_and_memory_fence/sync_interface/sync_interface.md)（`explains`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；同步接口正文说明“提供块内线程同步接口”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [RunOpApi 后缺 synchronize 致 .to 越序错](../../../../runbooks/compilation/runopapi_requires_synchronize_before_tensor_ops.md)（`related`）：焦点处理AI Core SIMT 的线程/块同步与内存栅栏；RunOpApi 后缺 synchronize 致 .to 越序错正文说明“cummin 算子 op_plugin 在 OpCommand::RunOpApi 后、idx32.to(kInt64) 前缺 synchronize，导致 .to 在 kernel 完成前执行而产生错误输出；判别要点是 RunOpApi 后对同一输出张量的 torch 操作前须”。候选提供线程块同步、grid 同步和 threadfence 的不同可见性边界。
- [原子操作（AI Core SIMT编程）](atomic_operations.md)（`related`）：同步指南明确 barrier/fence 不能替代并发同址读改写的原子操作，并说明跨 Thread Block 需组合 Global Memory、原子与 fence。
- [编程示例（AI Core SIMT编程）](programming_examples.md)（`related`）：同步机制（AI Core SIMT编程）说明SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [内存层级（AI Core SIMT编程）](memory_hierarchy.md)（`same_topic`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步机制（AI Core SIMT编程）正文界定“SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
<!-- cannbot:related:end -->
