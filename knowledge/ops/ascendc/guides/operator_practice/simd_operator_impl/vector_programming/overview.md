---
type: Guide
title: SIMD算子实现概述
description: 本节将以Add算子为例，带您快速构建Ascend C矢量算子程序，并学习矢量算子开发的典型场景以及处理方式。涉及的场景包括：
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

本节将以Add算子为例，带您快速构建Ascend C矢量算子程序，并学习矢量算子开发的典型场景以及处理方式。涉及的场景包括：

-   基础矢量算子：开发一个简单的Add矢量算子。
-   TBuf的使用：在算子计算过程中使用临时空间存储运算的中间结果。
-   多核Tiling切分：当算子需要多核并行计算或支持动态shape时，对输入数据进行切分、分块计算，并将不同数据块分配到多个AI Core上处理。
    -   主块均分：算子在AI处理器的多个核上运行，所有核的计算数据量相等且32字节对齐。
    -   尾块均分：算子在AI处理器的多个核上运行，所有核的计算数据量相等，每个核上除最后一个数据块（尾块）外，其余数据块的数据量相等，每个核都需要处理尾块数据的计算。
    -   尾核切分：算子在AI处理器的多个核上运行，数据无法平均分配到每个核。将所有核分为多个整核和多个尾核，整核的计算数据量相等，尾核的计算数据量相等。
    -   尾核尾块切分：算子在AI处理器的多个核上运行，数据无法平均分配到每个核，同时每个核内的数据无法均分，除最后一个数据块（尾块）外，其余数据块的数据量相等，每个核都需要单独处理尾块数据的计算。
-   DoubleBuffer场景：开启double buffer，算子中的多条流水并行执行。
-   Broadcast场景：算子中两个输入的shape（形状）不相等，需要将一个输入的shape进行Broadcast（广播）后，再执行计算。
-   非对齐场景：更多数据非32字节对齐场景的处理方案。

>进行数据搬运和Vector计算时，对于搬运的数据长度和操作数的起始地址有如下的对齐要求：
>- 使用DataCopy接口进行数据搬运，搬运的数据长度和操作数的起始地址（Unified Buffer上）必须保证32字节对齐。
>- 通常情况下，进行Vector计算时，操作数的起始地址必须保证32字节对齐，执行计算的基本单位为32字节。

<!-- cannbot:related:start -->
## 相关

- [SIMD计算概述](../../../../apis/simd_api/basic_api/memory_vector_compute/simd_compute/overview.md)（`explains`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；SIMD计算概述正文界定“矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
- [DoubleBuffer](../../../technical_appendix/concepts_and_terms/performance_optimization/double_buffer.md)（`related`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；DoubleBuffer正文界定“执行于AI Core上的指令队列主要包括如下几类，即Vector指令队列、Cube指令队列和MTE指令队列。不同指令队列间的相互独立性和可并行执行性，是DoubleBuffer优化机制的基石”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
- [SIMD算子实现概述](../overview.md)（`related`）：SIMD算子实现概述 与《SIMD算子实现概述》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [开启DoubleBuffer](../../simd_operator_optimization/pipeline_scheduling/enable_double_buffer.md)（`related`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；开启DoubleBuffer正文界定“【描述】执行于AI Core上的指令队列主要包括如下几类，Vector指令队列（V）、Cube指令队列（M）、Scalar指令队列（S）和搬运指令队列（MTE1/MTE2/MTE3）。不同指令队列间的相互独立性和可并行执行特性，是Doubl”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
- [SIMD算子实现概述](multi_core_tiling/overview.md)（`same_topic`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；SIMD算子实现概述正文界定“Ascend C核函数是在Device侧执行的并行函数。为了提高算子的执行效率，通常采用多核并行计算，将输入数据切分后分配到不同的逻辑核上处理；同时，由于单个核的Local Memory容量有限，无法一次完整容纳算子的输入和输出数据，需要分”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
- [基础矢量算子](basic_vector_operator.md)（`same_topic`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现概述》说明本节将以Add算子为例，带您快速构建Ascend C矢量算子程序，并学习矢量算子开发的典型场景以及处理方式。涉及的场景包括：。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
<!-- cannbot:related:end -->
