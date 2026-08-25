---
type: API
title: 内存空间限定符
description: 在SIMD与SIMT混合编程中使用内存空间限定符__gm__来表示分配于设备侧全局内存的对象，全局内存对象可以声明为标量、用户自定义结构体的指针。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/memory_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 内存空间限定符

SIMD 与 SIMT 混合编程使用两种内存空间限定符。

__gm__：表示设备侧全局内存（Global Memory）对象，可声明为标量或用户自定义结构体的指针。

__ubuf__：表示 Unified Buffer 中的动、静态内存。静态内存大小在编译期确定，通过数组分配（如 __ubuf__ half staticBuf[1024]）；动态内存大小在核函数启动时配置，通过 extern 数组声明（如 extern __ubuf__ half dynamicBuf[]）。

<!-- cannbot:related:start -->
## 相关

- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：限定符卡规定混合编程的 __gm__/__ubuf__，而故障卡用编译器展开证明纯 SIMT kernel 形参不能照搬 __gm__，给出明确的模式边界。
- [内存层级（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`explains`）：内存限定符把 __gm__/__ubuf__/私有存储映射到指南描述的 GM、共享 UB 和线程私有层级。
- [算子实现（SIMD与SIMT混合算子实现）](../../../../guides/operator_practice/simd_simt_hybrid_operator_impl/operator_impl.md)（`explains`）：实现同时传递 GM 输入、UB 中间区和 VF 参数，该限定符卡明确 __gm__/__ubuf__ 对象的地址空间含义，支撑接口签名和共享 UB 数据流。
- [函数执行空间限定符](function_execution_space_qualifier.md)（`related`）：《内存空间限定符》明确“在SIMD与SIMT混合编程中使用内存空间限定符__gm__来表示分配于设备侧全局内存的对象，全局内存对象可以声明为标量、用户自定义结构体的指针。”；它与《函数执行空间限定符》的“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
