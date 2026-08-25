---
type: Guide
title: 编程示例（AI Core SIMT编程）
description: 基于SIMT进行算子开发需要使用的内置关键字和API请参见SIMT BuiltIn关键字、SIMT语言扩展层C API。当前SIMT编程暂不支持部分语法结构，相关限制请参考语法限制。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/programming_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 编程示例

基于SIMT进行算子开发需要使用的内置关键字和API请参见SIMT BuiltIn关键字、SIMT语言扩展层C API。当前SIMT编程暂不支持部分语法结构，相关限制请参考语法限制。
考虑如下计算场景：从形状为100000 * 128的二维向量中获取指定索引所对应的12288行数据。算子输出output第i行数据的计算公式为：
在核函数中完成一行数据量的计算逻辑，通过配置多个线程完成不同行的数据计算操作。核函数的实现逻辑具体为：
-   通过每个线程独有的线程索引找到当前线程需要计算的数据偏移量。
一个线程完成一次核函数的计算操作，核函数内通过计算blockIdx.x * blockDim.x + threadIdx.x得到索引偏移，其中blockIdx是当前线程块的索引，blockDim是每个线程块启用的线程数，threadIdx是当前线程在线程块内的索引，更多详细介绍请参考SIMT BuiltIn关键字。
-   通过下标偏移将偏移位置的输入数据拷贝到输出中，从而完成获取指定数据的功能。
核函数的实现参考如下代码。完整的样例请参考简单gather算子样例。
算子需要处理总共12288行数据，每行数据由核函数完成处理，因此需要12288个线程来完成对所有数据的处理。在Host侧通过>>调用核函数，同时设置启动48个线程块、每个线程块包含256个线程，示例代码如下。

<!-- cannbot:related:start -->
## 相关

- [Hello World](../../../getting_started/quick_start/simt_programming/hello_world.md)（`related`）：Hello World说明本入门示例基于Ascend C SIMT实现Hello World算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [ThreadArchitecture](thread_architecture.md)（`related`）：ThreadArchitecture说明SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [内存层级（AI Core SIMT编程）](memory_hierarchy.md)（`related`）：内存层级（AI Core SIMT编程）说明SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [同步机制（AI Core SIMT编程）](synchronization.md)（`related`）：同步机制（AI Core SIMT编程）说明SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性，避免读到未完成写入的数据。同步接口主要分为两类：；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [核函数（AI Core SIMT编程）](kernel_function.md)（`related`）：核函数（AI Core SIMT编程）说明正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [Gather算子快速入门](../../../getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`same_topic`）：Gather算子快速入门 与《编程示例（AI Core SIMT编程）》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
<!-- cannbot:related:end -->
