---
type: Guide
title: SIMD与SIMT混合编程概述
description: 为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 概述

为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型。

>该编程模型适用于如下型号：
>-   Ascend 950PR/Ascend 950DT

## 混合编程的定位

在该模型下，矩阵计算单元和向量计算中的SIMD计算单元共同提供超过90%的算力，为密集计算提供高性能与高算力利用率；向量计算中的SIMT则作为灵活性补充，专门应对复杂控制流、离散访存等不规则场景，提升此类场景下算法开发与优化的效率。
因此，在SIMD与SIMT混合编程中，SIMT不用于替代SIMD处理连续、密集的计算任务，而是用于处理算子中的局部不规则逻辑。典型方式是在核函数中通过SIMT VF处理分支判断、索引映射、离散访存等局部片段，再由SIMD继续处理向量或矩阵计算，从而兼顾灵活性和高吞吐。

## 混合编程的适用场景

如上文所述，混合编程适用于算子功能既包含SIMD擅长的连续规整计算，也包含SIMT擅长的离散访问等任务的场景。以下列举部分混合编程的适用场景：

-   复杂分支判断的算子，适合使用SIMT完成计算任务，而输入输出的数据搬运较规整连续，适合使用SIMD搬运接口完成数据拷贝。例如floor_mod样例。

-   离散访问场景，适合使用SIMT完成计算任务，当所需访问的数据量远小于Unified Buffer可用空间时，可以使用SIMD搬运接口完成数据拷贝，使SIMT编程能够直接从Unified Buffer读取数据，提高内存访问效率。

-   某些算子，在大Shape场景，使用SIMD并行计算效率更高；而在小Shape不规整场景，则适合使用SIMT完成计算。因此可以区分算子场景，分别使用两种编程方式实现算子功能，提升泛化场景整体性能。

## 指南概览

混合编程作为高级编程方式，在阅读本章节内容前需对SIMD编程模型和SIMT编程模型有一定的了解。本章节将从以下几个方面展开介绍混合编程：

-   **抽象硬件架构**：介绍了SIMD与SIMT混合编程场景的硬件架构，介绍VF（Vector Function）运行机制及SIMT VF、SIMD VF等概念。

-   **核函数与VF函数**：详细介绍了混合编程场景的核函数定义、调用方式及执行配置，VF函数及各类函数的调用关系。

-   **内存层级**：展示混合编程场景的内存层级，重点介绍了VF之间的通信方式，UB内存作为共享内存是如何分配与管理的。

-   **编程示例**：以实际样例展示混合编程关键语法，包括`asc_vf_call`调用SIMT VF函数和`<<<>>>`核函数启动配置。

强烈建议开发者阅读混合编程场景的扩展语法与约束说明，掌握基本扩展语法及使用约束后开发自定义算子。

<!-- cannbot:related:start -->
## 相关

- [扩展语法内置变量](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：扩展语法内置变量 与《SIMD与SIMT混合编程概述》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [SIMD与SIMT混合算子性能优化概述](../../../../operator_practice/simd_simt_hybrid_optimization/overview.md)（`related`）：SIMD与SIMT混合算子性能优化概述说明AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适合处理分支判断、索引映射、离散访存等不规则逻辑，在程序中结合使用两种编程方式，可以兼顾硬件高吞吐和编程灵活性。
- [抽象硬件架构（SIMD与SIMT混合编程）](abstract_hardware_architecture.md)（`related`）：SIMD与SIMT混合编程概述说明为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型；对抽象硬件架构（SIMD与SIMT混合编程）而言，混合编程概述定义 SIMD/SIMT 分工，性能章节给出分支与访存选择，SIMT 分支实现卡提供落地接口。
- [编程示例（SIMD与SIMT混合编程）](programming_examples.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“SIMD与SIMT混合编程概述”定义：为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
- [通过SIMT实现分支判断](../../../../operator_practice/simd_simt_hybrid_optimization/compute_optimization/simt_branch_judgment.md)（`related`）：通过SIMT实现分支判断说明>该性能优化建议适用于如下型号：。
- [AI Core SIMD编程模型概述](../../../programming_model/ai_core_simd_programming/overview.md)（`same_topic`）：AI Core SIMD编程模型概述 与《SIMD与SIMT混合编程概述》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [核函数与VF函数（SIMD与SIMT混合编程）](kernel_and_vf_functions.md)（`same_topic`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMD与SIMT混合编程概述正文说明“为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
<!-- cannbot:related:end -->
