---
type: Guide
title: 异构系统（编程模型）
description: 一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device
  Memory。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/heterogeneous_system.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 异构系统

一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory。

基于昇腾的应用程序通常包含两部分：一部分运行在Host CPU上，使用标准C/C++编程；另一部分运行在NPU上，使用Ascend C编程语言编写。运行在NPU上的代码称为核函数Kernel，需由Host代码调用执行。此外，Host端需要通过CANN Runtime API完成以下操作：在Host Memory与Device Memory之间拷贝数据、启动NPU上的核函数、等待核函数执行完成等。Host代码与核函数可编写在同一个 .asc后缀文件中，由毕昇编译器完成异构编译。

为提升计算效率，NPU上通常有多个计算核并发执行，每个核一般处理不同的数据。每个NPU的计算核称为AI Core（AI处理器的计算核心）。传统上，AI Core遵循SIMD（Single Instruction Multiple Data，单指令多数据流）模型，通过一条指令同时操作多个数据实现并行计算。从Ascend 950PR/Ascend 950DT架构开始，作为SIMD的补充（主要用于辅助离散类矢量算子开发），AI Core也支持SIMT（Single Instruction Multiple Thread，单指令多线程）模型，通过一条指令驱动多个线程并行执行。

下图演示了运行在Host CPU上的代码通过调用CANN Runtime API将核函数下发到AI Core的流程。由于Host Memory与Device Memory拥有独立的内存空间，需要显式调用Runtime API进行数据传输。典型流程为：Host代码先将输入数据从Host Memory传输到Device Memory，随后启动Device侧核函数并等待其执行完成，最后将计算结果从Device Memory拷贝回Host Memory。

**图1**  Kernel调度示意图

> 关于Task/Stream等Runtime运行时管理的详细介绍，请参考[《Runtime运行时API》](https://hiascend.com/document/redirect/CannCommunityRuntimeApi)。

<!-- cannbot:related:start -->
## 相关

- [AI CPU编程（编程模型）](ai_cpu_programming.md)（`related`）：异构系统（编程模型）说明一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory。
- [内存层级（AI Core SIMT编程）](ai_core_simt_programming/memory_hierarchy.md)（`related`）：焦点处理SIMT 内存层级与地址空间、同步可见性；异构系统（编程模型）正文界定“一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [异构系统与编程模型](../../getting_started/quick_start/heterogeneous_system_and_programming_model.md)（`same_topic`）：“异构系统（编程模型）”定义：一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory。；“异构系统与编程模型”定义：> 本文作为算子编程快速入门章节，将从昇腾异构系统基础入手，逐步拆解编程模型核心要素，帮助您快速建立昇腾算子编程的整体认知，为后续实操开发奠定基础。。实质衔接：三者都区分 Host CPU/内存与 Device NPU/内存；快速入门建立模型，算子实践进一步给出 Host/Device 代码与数据流。
- [异构计算（算子实践）](../../operator_practice/heterogeneous_computing.md)（`same_topic`）：两篇指南都建立 Host CPU/Memory 与 Device NPU/Memory 的异构模型；编程模型页给出 Runtime 调度和数据传输，算子实践页把同一模型落实为 Host Tiling 与 Device Kernel 分工。
<!-- cannbot:related:end -->
