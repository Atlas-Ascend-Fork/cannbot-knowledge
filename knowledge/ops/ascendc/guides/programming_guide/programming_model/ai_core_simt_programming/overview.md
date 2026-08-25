---
type: Guide
title: AiCoreSimtProgrammingOverview
description: SIMT编程模型适用于离散数据访问和复杂控制流场景，基于Grid-Block-Thread三级线程层级在AIV核上实现线程级并行计算。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AI Core SIMT编程模型概述

## 引言
SIMT（Single Instruction Multiple Thread，单指令多线程）编程是AI Core编程方式的一种重要补充，特别适用于离散数据访问、复杂控制逻辑和分支发散等场景。Ascend C支持与业界一致的SIMT编程模型，通过线程级并行实现数据并行计算，每个线程允许指令对数据进行独立寻址与计算，从而实现了更高的编程灵活性。本章将以SIMT编程模型为主线，遵循「宏观架构—线程调度—代码落地」的递进逻辑，完整覆盖SIMT算子开发全链路：阐述多线程并行架构的执行机制，拆解线程块内Warp调度的底层逻辑，并完成算子Kernel计算逻辑的开发。
## 异构并行计算核心模型：SIMT编程范式
SIMT编程支持业界通用的线程架构：Grid-Block-Thread，以线程作为最小执行单元，通过大规模线程并发实现数据并行计算。所有SIMT算子的并行逻辑、数据拆分策略、线程调度机制，均基于该编程范式实现。
三级线程层级：
- 网格（Grid）：由多个线程块（Thread Block）组成，使用内置变量gridDim表示启用的线程块个数，Grid维度通过dim3三维结构表示。
- 线程块（Thread Block）：由若干线程组成，使用内置变量blockDim表示一个线程块启用的线程个数（一个线程块最多可启用2048个线程）。各线程块通过线程块索引blockIdx进行标识。
- 线程（Thread）：最小执行单位，每个线程拥有独立的寄存器，可通过线程索引threadIdx标识，负责完成特定的数据计算任务。
Warp调度机制：
每个线程块被切分成多个Warp依次调度执行，Warp是执行相同指令的线程集合，每个Warp包含32个线程。每个AIV核包含多个Warp调度器（Warp Scheduler），当某个Warp因全局内存访问处于阻塞状态时，Warp调度器会立刻切换到就绪的Warp，确保计算单元处于忙碌状态，从而掩盖访存的延迟并实现硬件利用率最大化。
> 📌 提示：基于SIMT编程模型的程序，在AIV核上执行多个结构相同的线程块，执行的总线程数等于gridDim × blockDim。每个线程指向相同的代码逻辑，但处理不同的数据片段，实现数据并行。
## 硬件底层支撑：SIMT单元架构与内存层级
向量处理单元AIV核是SIMT编程的核心硬件载体，采用「Warp调度器 + 计算单元 + 分级存储体系」的架构，下文将详细介绍SIMT核心硬件组件及SIMT编程的内存层级体系。
### 核心硬件组件
- Warp调度器：每个AIV核包含多个Warp调度器，负责线程块的切分与调度。Warp调度器将线程块划分为多个Warp，依次发射执行，实现高效的线程级并行调度。
- 计算单元：AIV核内的向量计算单元，负责执行各类向量运算指令。同一Warp内的32个线程执行相同指令，但对不同数据地址进行操作，实现单指令多线程并行计算。
- 寄存器文件：每个线程拥有独立的寄存器空间，用于存储局部变量和计算中间结果。寄存器数量受线程块内线程数量影响，线程数量越多，每个线程可用的寄存器数量越少。
- 共享内存：线程块内所有线程共享的内存空间，位于AIV核内部，具有高带宽、低延迟特性，可作为用户管理的高速缓存，支持线程间数据交互。
