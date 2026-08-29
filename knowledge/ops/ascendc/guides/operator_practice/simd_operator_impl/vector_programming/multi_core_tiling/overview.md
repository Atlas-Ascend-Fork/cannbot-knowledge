---
type: Guide
title: SIMD算子实现概述
description: Ascend C核函数是在Device侧执行的并行函数。为了提高算子的执行效率，通常采用多核并行计算，将输入数据切分后分配到不同的逻辑核上处理；同时，由于单个核的Local
  Memory容量有限，无法一次完整容纳算子的输入和输出数据，需要分批搬运数据进行计算。这种对输入数据进行切分、分块计算的过程称为Tiling。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

Ascend C核函数是在Device侧执行的并行函数。为了提高算子的执行效率，通常采用多核并行计算，将输入数据切分后分配到不同的逻辑核上处理；同时，由于单个核的Local Memory容量有限，无法一次完整容纳算子的输入和输出数据，需要分批搬运数据进行计算。这种对输入数据进行切分、分块计算的过程称为**Tiling**。

切分数据的算法称为Tiling算法或Tiling策略；根据算子shape等信息计算切分相关参数（如每次搬运的块大小、循环次数等）的程序，称为**Tiling实现**，也叫Tiling函数（Tiling Function）。基础矢量算子与TBuf的使用样例均在单核上运行，不涉及Host侧Tiling实现。

由于Tiling实现完成的均为标量计算，而AI Core并不擅长这类计算，因此通常将其独立出来由Host侧执行；对于动态shape算子，切分参数无法在编译期确定，也需要在Host侧计算。

开发者需要分析并设计Tiling参数、定义Tiling结构体，在Host侧通过上下文获取输入输出shape信息，根据shape信息计算Tiling参数并设置到对应的Tiling结构体中；随后通过核函数入口参数将Tiling信息传入核函数。核函数内部解析Host侧传入的Tiling结构体，根据Tiling信息控制数据搬入、搬出Local Memory的流程，并完成计算逻辑。

**图 1**  算子实现组成

如上图所示，算子实现由Device侧的Kernel实现与Host侧的Tiling实现两部分组成：Kernel实现负责在Device侧完成数据搬运、矢量计算、内存管理和任务同步等逻辑；Tiling实现用于在Kernel执行前，根据输入shape等信息在Host侧计算Kernel所需的切分参数。对于输入和输出shape固定、切分策略固定的简单算子，Host侧Tiling实现可以省略；对于动态shape或多核并行场景，每个核处理的数据量、核内分块数量等参数通常需要在Host侧计算后传递给Kernel使用。

对输入数据进行切分时应遵循以下原则：

1. 以DataBlock为最小切分单位。受硬件限制，进行Unified Buffer相关的数据搬运和矢量计算时，搬运的数据长度和操作数的起始地址都需要保证32字节对齐，即以DataBlock为单位进行操作，一个DataBlock大小为32字节；输入数据不满足DataBlock大小对齐要求时，需按DataBlock大小向上对齐。

2. 充分利用Unified Buffer空间。AI Core与外部存储交互时会产生性能开销，频繁地进行数据搬运会导致性能瓶颈，因此应尽可能充分利用Unified Buffer空间，减少从Global Memory搬运数据的次数。

3. 均衡利用多核计算能力。AI处理器包含多个AI Core，应将计算均衡分配到各核上，充分发挥多核并行优势。

本章基于矢量计算多核Tiling切分策略样例，以两个一维Tensor相加的Add矢量算子为例，对多核Tiling切分的典型场景进行说明。样例实现文件为vector_tiling_strategy.asc。

**图 2**  多核Tiling示意图
