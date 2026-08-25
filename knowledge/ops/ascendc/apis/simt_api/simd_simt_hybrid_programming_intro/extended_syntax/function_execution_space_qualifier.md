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

<!-- cannbot:related:start -->
## 相关

- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`exemplifies`）：RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃 与《函数执行空间限定符》的实质衔接是：该卡定位 __simd_vf__ 加 Reg 调用导致 BiSheng 139/70；所选编译故障复现相邻 VF 崩溃机制，asc_vf_call、执行限定符和 Reg 编程材料解释受禁路线的真实契约。
- [SIMT VF 栈数组动态索引致输出全零](../../../../runbooks/precision/simt_vf.md)（`exemplifies`）：SIMT VF 栈数组动态索引致输出全零：本卡暴露 __simt_vf__ 内局部数组动态索引的编译器语义缺口；官方执行空间限定符界定 VF/callee契约，helper限定符和Block元数据卡给出同一执行域内已验证的代码生成禁区。 目标卡《函数执行空间限定符》补充：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。
- [SIMT helper 误标 __simt_vf__ 导致编译失败](../../../../runbooks/compilation/simt_vf_helpers_use_simt_callee.md)（`exemplifies`）：限定符文档明确 __simt_vf__ 是启动入口、__simt_callee__ 是可被调用 helper，为编译错误提供规范依据。
- [SIMT 核类型推导失败 — 补 __vector__](../../../../runbooks/compilation/direct_launch_kernel_requires_vector_qualifier.md)（`exemplifies`）：SIMT 核类型推导失败 — 补 __vector__：故障的直接修复是为承载 asc_vf_call 的 shell补 __vector__；混合 VF与空 kernel卡复现同一 kernel-type推导机制，官方限定符页给出合法调用层级，header/GM_ADDR卡补齐启动边界。 目标卡《函数执行空间限定符》补充：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。
- [simd_vf 互调导致 helper 编译失败](../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：simd_vf 互调导致 helper 编译失败 与《函数执行空间限定符》的实质衔接是：顶层 __simd_vf__ 只能调用 __simd_callee__ helper；asc_vf_call、执行限定符、kernel/VF 指南和相邻 VF 编译故障共同固定三层调用结构。
- [SIMD&SIMT BuiltIn关键字](../../../../guides/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《函数执行空间限定符》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [技术附录函数](../../../../guides/technical_appendix/cpp_standard_support/syntax_restrictions/functions.md)（`explains`）：函数限制卡列出 __simt_vf__ 的参数、地址空间和间接调用限制；限定符卡给出 __simt_vf__/__simt_callee__/__callee__ 的合法调用层级，解释这些限制属于哪类函数。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；函数执行空间限定符正文说明“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [ProgrammingModel](../programming_model.md)（`related`）：《函数执行空间限定符》明确“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
- [内存空间限定符](memory_space_qualifier.md)（`related`）：《内存空间限定符》明确“在SIMD与SIMT混合编程中使用内存空间限定符__gm__来表示分配于设备侧全局内存的对象，全局内存对象可以声明为标量、用户自定义结构体的指针。”；它与《函数执行空间限定符》的“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。”在实际调用参数、数据流或结果校验上直接衔接。
- [函数执行空间限定符](../../simt_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`same_topic`）：两张“函数执行空间限定符”卡描述同一 Host/Device 调用约束：SIMT 页定义 __host__/__global__/__aicore__，混合编程页在此基础上加入 __simt_vf__/__simd_vf__ 与 callee 层级。
<!-- cannbot:related:end -->
