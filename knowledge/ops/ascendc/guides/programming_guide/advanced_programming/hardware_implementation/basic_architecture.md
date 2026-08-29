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
