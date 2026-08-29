---
type: Guide
title: 编程模型概述
description: 介绍Ascend C编程模型，涵盖SIMD与SIMT并行执行模型、AI Core硬件基础及编程路径选择。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/programming_model_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 编程模型概述

如异构系统章节所述，基于昇腾处理器的应用程序通常分为两部分：Host代码与Device代码。其中，Host代码运行在CPU上，负责设备资源管理、Host Memory与Device Memory数据搬运及任务调度等；Device代码运行在NPU（神经网络处理器）上，专门执行实际的计算任务。本编程指南重点讲解如何基于Ascend C编程语言编写Device代码，以及如何通过Host代码完成Device代码的调度与执行。
## 并行执行模型：SIMD与SIMT
为编写高性能的Device端代码，首先需要理解底层的并行计算原理。在高性能并行编程领域，SIMD和SIMT是两种主流的并行执行模型，它们定义了指令驱动多计算单元协同工作的核心机制，是提升程序数据吞吐量、优化计算性能的关键技术，也是学习Ascend C编程的核心内容。
### SIMD（单指令多数据流）
核心概念：SIMD（Single Instruction Multiple Data）是一种 数据并行 模型，核心逻辑是：一条指令在同一个时钟周期内，对多个数据元素执行完全相同的操作，实现数据的批量并行处理。
核心特征：
- 单指令驱动：所有并行计算单元同步执行同一条指令，操作完全一致；
- 数据同构：要求参与计算的数据类型统一、长度相同，确保指令可批量处理；
- 同步执行：所有数据的操作在同一个指令周期内完成，无独立调度逻辑，执行节奏完全统一。
适用场景：主要适配数据密集、操作规整、无分支或分支极少的计算任务，典型场景包括：
- 图像像素处理（如灰度化、滤波、像素缩放）；
- 音频信号分析（如降噪、信号预处理）；
- 矩阵乘法、卷积等深度学习核心运算；
- 逐元素数学函数（如向量加减、乘除、指数/对数运算）。
SIMD核函数Kernel编程四步法：SIMD编程遵循SPMD模型（Single Program Multiple Data，单程序多数据），即每个AI Core运行同一份核函数，但负责处理不同的数据块，具体步骤如下：
1. Tiling（分块）设计：对全局超大数据进行均匀切分，为各AI Core分配大小均衡的独立数据分片，精准适配SPMD多核并行架构，规避单核算力瓶颈，实现全域负载均衡。
2. 数据搬入：调用SIMD专用API，将计算所需的数据从Device Memory（通常为HBM）搬运到AI Core的本地缓存，减少全局内存访问延迟。
3. 数据计算：调用向量指令，一次处理多个同构数据；需注意，数据搬运与计算过程通常是异步执行的，需插入同步指令，确保计算时数据已就绪，保证结果准确。
4. 数据搬出：调用SIMD专用API，将本地缓存中完成计算的结果，搬运回Device Memory，供后续任务使用。
### SIMT（单指令多线程）
核心概念：SIMT（Single Instruction Multiple Threads）是一种 线程并行 模型，核心逻辑是：一条指令同时驱动多个独立线程，每个线程仅处理一个数据元素；指令同步下发，但线程可根据代码分支（如if-else）独立执行，灵活性更高。
