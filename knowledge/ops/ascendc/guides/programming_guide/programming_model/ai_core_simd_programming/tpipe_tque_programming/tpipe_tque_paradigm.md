---
type: Guide
title: TPipe和TQue编程范式
description: 上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。
tags: [task.lookup, topic.implementation.pipeline]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TPipe和TQue编程范式

上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。
本章将上述原理固化为可直接编码的标准化编程范式。上一章回答为什么这样设计，本章则聚焦如何按此设计编写代码。TPipe‑TQue编程范式的本质，是队列管道思想在AI Core上的工程化落地——它将流水线拆分、队列同步、内存生命周期管理、异步并行调度等复杂底层逻辑，封装为一套统一、固定的开发流程，帮助开发者快速编写规范、可流水且高性能的算子核函数。
该范式定义了算子核函数实现的标准化固定流程。开发者严格遵循此范式，无需手动编写底层同步逻辑，也不必独自处理数据依赖与时序阻塞，即可快速搭建稳定、高效的算子代码框架。
从硬件执行形态看，AI Core内部的向量单元、矩阵单元和数据搬运单元天然支持异步并行与流水线执行。TPipe‑TQue编程范式完全贴合这一硬件特性，将硬件的多级流水行为抽象为软件层面统一的数据搬入—计算—数据搬出三段式流水线开发模型。
流水并行的核心逻辑可通过示意图直观理解：完整算子任务被拆分为多个有序子阶段，不同硬件单元负责不同工序；同一数据分片需在各阶段间串行流动，以保证数据依赖合法；不同数据分片则可在不同阶段同时处理，实现流水线吞吐叠加，与经典C/C++管道程序的执行逻辑完全一致。
结合上一章的阐述可总结出：Ascend C流水线体系由两大核心模块共同支撑：
- TPipe 资源管理器：统一管理系统内存资源和用于同步的事件等；
- TQue 队列：完成Stage任务之间的同步和通信。
基于这套机制，Ascend C固化了矢量、矩阵、融合三类算子的标准化流水线编程范式。下文将结合硬件特性与工程实例逐一展开。
-   矢量编程范式
-   矩阵编程范式
-   融合算子编程范式
## 矢量编程范式
如上图所示，矢量编程范式将算子实现流程划分为三个基本任务：CopyIn、Compute和CopyOut。
- CopyIn负责数据搬入：将输入数据从Global Memory搬运到Local Memory（VECIN表示矢量计算搬入数据的存放位置），搬运完成后将数据入队；
- Compute负责矢量指令计算：从队列取出数据后，在Local Memory上执行计算，计算完成后将结果入队；
- CopyOut负责数据搬出：从队列取出计算结果，将其从Local Memory（VECOUT表示矢量计算搬出数据的存放位置）搬运回Global Memory。
上述VECIN、VECOUT均属于TPosition（逻辑位置）概念。Ascend C通过抽象的TPosition表达不同层级的物理存储，以替代直接的片上物理存储概念，实现硬件架构的隐藏。除VECIN和VECOUT外，矢量编程中还会用到VECCALC，通常在定义临时变量时使用。
从编程角度看，具体流程（如下方伪代码所示）及流程图如下：
任务间数据传递所使用的内存、事件等资源，统一由TPipe管理。
