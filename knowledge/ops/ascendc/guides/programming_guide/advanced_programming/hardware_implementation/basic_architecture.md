---
type: Guide
title: 基本架构（硬件实现）
description: 如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型；对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参考中很多内容都以本章为基础进行介绍。
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/basic_architecture.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 基本架构

如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型；对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参考中很多内容都以本章为基础进行介绍。
AI Core负责执行矩阵、矢量计算密集的任务，其包括以下组成部分：
-   计算单元：包括Cube（矩阵）计算单元、Vector（矢量）计算单元和Scalar（标量）计算单元。
-   存储单元：包括L1 Buffer、L0A Buffer、L0B Buffer、L0C Buffer、Unified Buffer、BiasTable Buffer、Fixpipe Buffer等专为高效计算设计的存储单元。
-   搬运单元：包括MTE1、MTE2、MTE3和FixPipe，用于数据在不同存储单元之间的高效传输。
以Atlas A2 训练系列产品/Atlas A2 推理系列产品为例，硬件架构图如下：
本章节首先介绍硬件架构相关的关键概念和术语，以及AI Core的工作模式，为理解后续内容奠定基础。随后以Atlas A2 训练系列产品/Atlas A2 推理系列产品为例，提供AI Core基本架构的介绍：首先介绍计算单元、存储单元和搬运单元的基本功能与结构，然后通过典型的数据流和控制流示例，帮助开发者深入理解硬件架构的工作原理。针对不同产品型号对应的具体架构规格和细节说明需要参考后续架构规格章节。
## 关键概念和术语
-   Core
拥有独立Scalar计算单元的计算核。Scalar计算单元是核内的调度单元，承担了核内的指令发射等功能。
-   AI Core
AI处理器的计算核，负责执行矩阵、矢量计算密集的任务。
-   Cube Core
矩阵计算核，专注于矩阵计算。由Scalar调度单元、矩阵计算单元、搬运单元等组成，不包括矢量计算单元。
-   Vector Core
矢量计算核，专注于矢量计算，由Scalar调度单元、矢量计算单元、搬运单元等组成，不包括矩阵计算单元。
-   AIC
在AI Core分离模式下，一组Cube Core和Vector Core组合中的Cube Core。
-   AIV
在AI Core分离模式下，一组Cube Core和Vector Core组合中的Vector Core。
## AI Core的工作模式
-   分离模式
AI Core的一种工作模式，矩阵计算单元、矢量计算单元各自对应独立的Scalar调度单元，分离部署在Cube Core和Vector Core上。将Cube Core和Vector Core按照一定比例（1：N）进行组合，这样的组合视为一个AI Core，AI Core的核数以Cube Core为准。
-   耦合模式
AI Core的一种工作模式，矩阵计算单元、矢量计算单元对应同一个Scalar调度单元，部署在一个AI Core上。

<!-- cannbot:related:start -->
## 相关

- [NPU架构版本2002](architecture_spec/npu_arch_2002.md)（`related`）：基本架构说明 AI Core、存储与流水抽象，为理解 2002 规格中的具体单元提供公共模型。
- [NPU架构版本2002](hardware_constraints/npu_arch_2002.md)（`related`）：NPU架构版本2002 与《基本架构（硬件实现）》的实质衔接是：2002 architecture spec给出硬件组成，constraints给出 Generic Addressing/全局变量限制；GetCurNpuArch和 SoC 查证链用于确认当前目标确实落在2002。
- [NPU架构版本2201](architecture_spec/npu_arch_2201.md)（`related`）：2201 规格给出基础架构在 A2/A3 类芯片上的具体核数、存储和流水参数。
- [NPU架构版本3002](architecture_spec/npu_arch_3002.md)（`related`）：NPU架构版本3002 与《基本架构（硬件实现）》的衔接是：arch3002 卡给出该架构的核结构与存储约束；基础架构说明、运行时架构查询和 SoC→ini→NpuArch 查证链用于确认实际编译/运行落到该变体。
- [NPU架构版本3510](architecture_spec/npu_arch_3510.md)（`related`）：3510 规格给出 Ascend950 的具体硬件资源，是判断架构差异和可用 API 的依据。
- [内存层级（SIMD与SIMT混合编程）](../advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`related`）：存储层级页展开 GM/L2/片上 buffer 的数据流，直接支撑基础架构中的搬运与流水理解。
- [抽象硬件架构（AI Core SIMD编程）](../../programming_model/ai_core_simd_programming/abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《基本架构（硬件实现）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [抽象硬件架构（AI Core SIMT编程）](../../programming_model/ai_core_simt_programming/abstract_hardware_architecture.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“基本架构（硬件实现）”明确如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型；对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参考中很多内容都以本章为基础进行介绍。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
- [抽象硬件架构（SIMD与SIMT混合编程）](../advanced_ai_core_programming_model/simd_simt_hybrid_programming/abstract_hardware_architecture.md)（`same_topic`）：混合编程架构页在同一 AI Core 上展开 SIMD/SIMT 单元与调度关系，是基础架构的具体编程视角。
<!-- cannbot:related:end -->
