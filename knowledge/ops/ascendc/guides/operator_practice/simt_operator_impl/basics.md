---
type: Guide
title: 基础知识（SIMT算子实现）
description: 本节内容为使用SIMT API进行SIMT编程的指导。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_impl/basics.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 基础知识

本节内容为使用SIMT API进行SIMT编程的指导。

与SIMD编程不同，在SIMT编程中Global Memory上的数据可以被直接读取和使用。SIMT编程常通过组织线程的层次结构来实现数据切分，使用threadIdx等SIMT BuiltIn关键字计算线程应处理的数据索引，完成对应数据的计算，从而将函数的实现简化为标量计算。

SIMT是单指令多线程的编程抽象，允许一条指令驱动多个线程，每个线程可对各自的数据独立寻址，更加灵活，如下图所示，对于离散访问的算子，适合使用SIMT编程实现，例如Scatter类与Gather类算子。此外，线程可以独立执行，每个线程具有较高的灵活性，能够执行不同的逻辑分支以完成复杂的逻辑实现。
