---
type: Guide
title: 抽象硬件架构（AI Core SIMT编程）
description: AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂算子和不规则控制流的开发，缓解包含分支的发散计算并控制程序复杂度，从而提高硬件利用率和能效。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/abstract_hardware_architecture.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 抽象硬件架构

AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂算子和不规则控制流的开发，缓解包含分支的发散计算并控制程序复杂度，从而提高硬件利用率和能效。

如[图1](#fig35720259287)所示，AI处理器内部有多个Vector Core，每个Vector Core包含计算单元、Shared Memory（位于Unified Buffer）、寄存器，核外的Global Memory是全局内存空间，被所有Vector Core共享。

**图1**  SIMT抽象硬件架构图

以下是SIMT多线程计算涉及到的硬件资源的说明：

-   每个线程拥有独立的寄存器，用于存储局部数据，寄存器的数量受线程块内线程数量影响，线程数量越多，每个线程拥有的寄存器数量越少。
-   Unified Buffer按功能划分为多个区域，其中一部分内存空间作为线程块内所有线程的共享内存（Shared Memory），支持线程块内的线程进行数据交互；一部分作为Data Cache，用于缓存全局内存数据。
-   L2 Cache是所有Vector Core共享的高速缓存，位于Global Memory与各Vector Core的Data Cache之间，用于缓存全局内存数据以减少访问延迟。L2 Cache由硬件自动管理，用户无需显式配置。
-   SIMT模式中，读取Global Memory上的数据时，通过Data Cache单元完成数据中转，数据流经由Global Memory到Data Cache，再从Data Cache到寄存器。Data Cache是Unified Buffer中预留的一部分空间，实际大小由用户自主分配。

若您对上述内容中的线程、线程块等概念不熟悉，建议查阅线程架构了解更多SIMT线程架构知识；同时，您也可以通过阅读内存层级，了解如何在Unified Buffer中配置共享内存与Data Cache的空间大小。

<!-- cannbot:related:start -->
## 相关

- [AiCoreSimtProgrammingOverview](overview.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“AiCoreSimtProgrammingOverview”明确SIMT编程模型适用于离散数据访问和复杂控制流场景，基于Grid-Block-Thread三级线程层级在AIV核上实现线程级并行计算。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [ThreadArchitecture](thread_architecture.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“ThreadArchitecture”明确SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [内存层级（AI Core SIMT编程）](memory_hierarchy.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“内存层级（AI Core SIMT编程）”明确SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [基本架构（硬件实现）](../../advanced_programming/hardware_implementation/basic_architecture.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“基本架构（硬件实现）”明确如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型；对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参考中很多内容都以本章为基础进行介绍。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [抽象硬件架构（AI Core SIMD编程）](../ai_core_simd_programming/abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《抽象硬件架构（AI Core SIMT编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [核函数（AI Core SIMT编程）](kernel_function.md)（`same_topic`）：SIMT 抽象硬件架构解释核函数运行在由线程块、Warp 和标量/矢量资源组成的模型上，是理解 kernel 入口并发层级的前置。
<!-- cannbot:related:end -->
