---
type: API
title: 函数执行空间限定符
description: SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 函数执行空间限定符

SIMD 与 SIMT 混合编程涉及多种函数类型，遵循严格调用关系和层级约束。

主要限定符：__global__ __aicore__（算子入口，协调 VF 执行，Host 通过 <<<>>> 调用）、__aicore__（Device 侧辅助函数）、__simt_vf__（线程级并行计算任务，通过 asc_vf_call 调用）、__simd_vf__（向量级并行计算任务）、__simt_callee__（SIMT VF 子函数）、__simd_callee__（SIMD VF 子函数）、__callee__（编译期 Device 侧辅助函数）。

__simt_vf__：标记 SIMT VF 入口函数，无返回值，内可使用 threadIdx/blockIdx/blockDim/gridDim。入参仅支持内置数据类型及其指针/数组/结构体（指针需指向 GM 或 UB），只能调用 __simt_callee__ 或 __callee__ 函数。

__simt_callee__：SIMT VF 内部辅助函数，可使用 SIMT 内置变量，返回值和入参仅支持内置数据类型及指针，只能调用 __simt_callee__ 或 __callee__ 函数。
