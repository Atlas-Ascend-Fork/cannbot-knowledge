---
type: Guide
title: 算子功能设计
description: 本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_function_design.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子功能设计

本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。
本文以AddCustom算子作为示例。AddCustom的计算语义如下：
本文只给出功能设计阶段需要明确的内容。具体接口和代码写法会在后续章节展开。
## 前置理解：aclnn工程化算子开发方式由哪几部分组成
一个aclnn自定义算子工程通常需要完成三类代码。
第一类代码：算子原型定义，声明算子的接口信息，包括输入、输出和属性，以及支持的dtype、format。
第二类代码：Host侧Tiling实现，在Kernel执行前准备运行参数。Kernel在AI Core上运行前，需要知道本次输入一共有多少数据、如何切核并启动多少个Block、每个Block内部如何继续切分、是否需要额外workspace，以及是否需要设置调度模式等launch配置。
第三类代码：Kernel侧算子实现，在AI Core上执行的实际计算。Kernel侧根据Tiling传入的参数，从GM搬运数据到UB，在UB上完成计算，再把结果写回GM。
本文的功能设计，就是在写这三类代码前，先确定每一类代码需要表达什么。
## 围绕算子原型做功能设计
算子原型设计从算子语义开始。算子语义描述算子接收什么数据、执行什么计算、输出什么结果。这个步骤决定OpDef中的输入输出声明，也决定Tiling和Kernel需要围绕哪些数据设计。
AddCustom是逐元素加法算子。输入x和y在相同位置上的元素相加，结果写入输出z。每个元素的计算互相独立，适合按连续数据段切分到多个Block上并行处理。
根据这条语义，可以先确定算子对外暴露的原型边界。AddCustom对外暴露两个输入x、y和一个输出z。这三个Tensor已经可以完整表达z = x + y的计算语义，每次调用都需要提供，因此在原型边界上都属于必选参数。AddCustom没有额外属性，调用方只需要准备两个输入Tensor和一个输出Tensor。
如果算子带有标量、维度、阈值、开关等配置项，需要在功能设计阶段确定它们的承载方式。值较小且用于描述算子行为的配置项适合作为属性；需要按Tensor传入、参与动态图数据依赖或数据量较大的内容适合作为输入。属性识别和传递的完整示例请参考通过TilingData传递属性信息。
除此之外，还需要确定算子支持什么场景：
- 数据类型和数据格式。
- 确定性：算子在相同输入下是否产生相同输出。
将前两步确定的输入输出、dtype/format列表等合并，即得到完整的算子原型定义。完整的算子原型定义编写方法和API说明请参考算子原型定义。
完成算子原型设计后，功能设计可以继续拆解Host侧Tiling需要准备的运行参数，以及Kernel侧如何完成实际计算。
## 围绕Host侧Tiling做功能设计
Host侧Tiling设计的重点，是确定Kernel启动前需要准备哪些运行参数。Host侧Tiling负责把输入shape、属性等信息转换成Kernel运行时需要的参数，包括切核策略、Block内切分、workspace大小、TilingKey和必要的调度模式等。
