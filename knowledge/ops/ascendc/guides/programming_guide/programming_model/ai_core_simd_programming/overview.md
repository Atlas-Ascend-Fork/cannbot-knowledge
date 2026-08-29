---
type: Guide
title: AI Core SIMD编程模型概述
description: SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI
  Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AI Core SIMD编程模型概述

## 引言
SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。
## 异构并行计算核心模型：SPMD嵌套SIMD编程范式
昇腾NPU异构并行体系采用外层多核SPMD（Single Program Multiple Data）并行 \+ 内层单核SIMD细粒度并行的双层融合架构，是AI Core算子开发的核心理论根基。所有SIMD算子的并行逻辑、数据拆分策略、任务调度机制，均基于该编程范式实现。
多核集群层面遵循SPMD编程模型：将每个AI Core抽象成一个Block，通过内置变量block_idx作为Block索引。每个Block执行同一份算子Kernel代码，一般基于block_idx划分每个Block的数据处理范围，实现多核负载均衡与并行调度。
单核计算层面依托SIMD并行机制：单个AI Core内部基于SIMD机制实现细粒度并行，依靠硬件专用计算单元，单条指令批量完成多组同质数据的并行运算，充分挖掘单AI Core的极致算力潜力。
## 硬件底层支撑：AI Core计算单元架构与算子分类
AI Core是昇腾NPU的基础核心计算单元，采用「控制单元\+异构计算单元\+分级本地存储」的经典架构，各组件分工明确、协同联动。硬件的能力边界直接决定算子的计算形态与开发方式，下文将详细介绍AI Core核心硬件组件，以及基于硬件能力划分的标准化算子类型。
### AI Core核心硬件组件
- 标量处理单元：作为AI Core的控制中枢，主要负责地址偏移计算、指令调度与发射，统筹管控其他运算单元的指令执行流程，支撑分支、循环等各类控制流逻辑的正常运行。
- 向量处理单元Vector：遵循标准SIMD并行计算逻辑，专职执行各类向量指令，支持单指令多数据并行运算，适配元素级计算、逻辑运算、数据重组等灵活性要求高的计算场景。
- 矩阵运算单元Cube：高密度张量专用算力单元，面向矩阵乘加、高维张量卷积等算力密集型场景深度优化。硬件原生支持批量矩阵运算，典型能力为单次完成一组float16类型16×16矩阵乘法，是AI模型训练与推理场景的核心算力支撑。
- 本地存储：AI Core片内高速存储体系，用于缓存计算中间数据，规避频繁访问低速全局内存的性能损耗，降低访存延迟。其中Cube计算单元配套L1 Buffer、L0C Buffer等；Vector计算单元配套统一缓存UB（Unified Buffer）。
### 基于硬件单元的三类标准算子
根据算子核心计算逻辑对硬件单元的依赖差异，AI Core算子可划分为三大标准类型，通过专属修饰符标准化硬件资源调度规则，统一全域算子开发规范：
- 矢量类算子：核心计算逻辑完全由Vector计算单元承载，无矩阵密集运算，以元素级、逻辑类、数据重组类计算为主，适配访存密集、灵活度要求高的场景。核函数通过__vector__修饰。
