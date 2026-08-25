---
type: Guide
title: 核函数与VF函数（SIMD与SIMT混合编程）
description: SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 核函数与VF函数

SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。
SIMD与SIMT混合编程中涉及的函数类型如下表所示：
__global__ __aicore__：算子入口，协调VF执行。若只有在AIV核内执行的SIMD与SIMT混合编程场景，可使用__global__ __vector__来标识只启动AIV核。：Host侧通过>>调用
__aicore__：Device侧辅助函数：核函数或同级函数调用
__simt_vf__：线程级并行计算任务：通过SIMT提供的asc_vf_call接口调用
__simd_vf__：向量级并行计算任务：通过SIMD提供的asc_vf_call接口调用
__simt_callee__：SIMT VF的子函数：SIMT VF内部调用
__simd_callee__：SIMD VF的子函数：SIMD VF内部调用
__callee__：SIMD VF和SIMT VF的公共子函数：VF内部调用
各层函数间的调用关系如下：
- 核函数：是Device侧的入口函数，可以调用__aicore__函数和VF函数。
- simd vf函数：能被核函数或者__aicore__函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和__callee__函数。
- simt vf函数：使用__simt_vf__标记，能被核函数或者__aicore__函数通过asc_vf_call接口调用。simt vf函数内只能调用__simt_callee__函数和__callee__函数。
- __simd_callee__子函数：simd vf函数内部的子函数，子函数可能有返回值或者通过引用传参。__simd_callee__函数内只能调用__simd_callee__函数和__callee__函数。
- __simt_callee__子函数：simt vf函数内部的子函数，子函数可能有返回值或者通过引用传参。__simt_callee__函数内只能调用__simt_callee__函数和__callee__函数。
- __callee__公共函数：可供VF内部调用的公共子函数。__callee__函数内只能调用__callee__函数。
## 核函数的定义与执行配置
核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。
