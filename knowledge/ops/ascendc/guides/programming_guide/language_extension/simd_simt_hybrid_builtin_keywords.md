---
type: Guide
title: SIMD&SIMT BuiltIn关键字
description: SIMD与SIMT混合编程使用的函数执行空间限定符与SIMD编程一致，详细说明请参见SIMD BuiltIn关键字的函数执行空间限定符。
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# SIMD&SIMT BuiltIn关键字

## 函数执行空间限定符
SIMD与SIMT混合编程使用的函数执行空间限定符与SIMD编程一致，详细说明请参见SIMD BuiltIn关键字的函数执行空间限定符。
## VF函数执行限定符
### __simt_vf__
__simt_vf__用于标记SIMT VF入口函数，函数无返回值。函数定义示例如下：
SIMT VF函数定义中的关键修饰符说明如下：
__simt_vf__：函数标识符，标识SIMT VF函数。
inline：建议内联，实际是否内联由编译器决定。
__gm__：内存空间修饰符，标识内存空间为GM。
__ubuf__：内存空间修饰符，标识内存空间为UB。
只支持在核函数或__aicore__函数中调用SIMT VF函数，调用接口为asc_vf_call，示例如下：
SIMT VF函数有以下约束：
-   入参仅支持Ascend C的内置数据类型（int32_t、uint32_t、float、half等）及其组成的指针、数组、结构体类型，且指针类型必须指向GM或者UB内存。
-   函数返回类型必须是void。
-   SIMT VF内只能调用__simt_callee__函数或__callee__函数。
### __simt_callee__
__simt_callee__子函数是SIMT VF函数内部调用的辅助函数，函数内部可以使用SIMT内置变量。定义示例如下：
调用示例如下：
该函数有以下约束：
-   入参仅支持Ascend C的内置数据类型（int32_t、uint32_t、float、half等）及对应的指针类型。
-   函数返回值只能是Ascend C的内置数据类型（int32_t、uint32_t、float、half等）及对应的指针类型。
-   函数内只能调用__simt_callee__函数或__callee__函数。
### __simd_vf__与__simd_callee__
__simd_vf__用于标记SIMD VF入口函数，__simd_callee__是供SIMD VF内部调用子函数，详细说明请参见SIMD BuiltIn关键字的SIMD VF函数标识符。
## 地址空间限定符
SIMD与SIMT混合编程使用的地址空间限定符与SIMD编程一致，详细说明请参见SIMD BuiltIn关键字的地址空间限定符。
## 核函数配置
### 核函数定义
核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：
关键修饰符说明如下：
-   __global__：必需修饰符，作用为标识核函数，表明可在Host侧通过>>调用。
-   __vector__：必需修饰符，作用为标识函数是在Device侧AIV核上执行。
