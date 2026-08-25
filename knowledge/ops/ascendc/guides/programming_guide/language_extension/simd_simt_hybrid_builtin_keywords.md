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

<!-- cannbot:related:start -->
## 相关

- [VF调用](../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《VF调用》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [asc_vf_call](../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《asc_vf_call》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [函数执行空间限定符](../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《函数执行空间限定符》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [扩展语法内置变量](../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：扩展语法内置变量 与《SIMD&SIMT BuiltIn关键字》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](../../../runbooks/precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《AR 跨块循环放在 __simd_vf__ 只执行首块》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [SIMT __ubuf__ 静态数组 UB 占用不随分支释放](../../../runbooks/compilation/simt_ubuf_ub.md)（`related`）：《SIMT __ubuf__ 静态数组 UB 占用不随分支释放》说明SIMT kernel 的 __ubuf__ 静态数组是编译期分配、生命周期绑所在函数栈的 UB 资源，运行时分支只控制是否解引用、不控制是否占用；把“需要该数组”与“不需要该数组”两条路径塞进同一函数，会令不解引用的路径也白白占住 UB。给出按解引用关系拆函数的判别方法。；《SIMD&SIMT BuiltIn关键字》说明SIMD与SIMT混合编程使用的函数执行空间限定符与SIMD编程一致，详细说明请参见SIMD BuiltIn关键字的函数执行空间限定符。。二者在SIMT静态__ubuf__数组按函数栈常驻，地址空间限定、UB预算及TBuf管理方案直接决定如何拆函数或改为受管内存上存在可执行的直接衔接。
- [SIMT helper 误标 __simt_vf__ 导致编译失败](../../../runbooks/compilation/simt_vf_helpers_use_simt_callee.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《SIMT helper 误标 __simt_vf__ 导致编译失败》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [__simd_vf__ if constexpr 致 hoisted 报错](../../../runbooks/compilation/simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《SIMD&SIMT BuiltIn关键字》说明SIMD与SIMT混合编程使用的函数执行空间限定符与SIMD编程一致，详细说明请参见SIMD BuiltIn关键字的函数执行空间限定符。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [simd_vf 互调导致 helper 编译失败](../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《simd_vf 互调导致 helper 编译失败》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [核函数与VF函数（SIMD与SIMT混合编程）](../advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《核函数与VF函数（SIMD与SIMT混合编程）》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [SIMD BuiltIn关键字](simd_builtin_keywords.md)（`same_topic`）：SIMD&SIMT BuiltIn关键字 与《SIMD BuiltIn关键字》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [SIMT BuiltIn关键字](simt_builtin_keywords.md)（`same_topic`）：SIMD&SIMT BuiltIn关键字 与《SIMT BuiltIn关键字》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
<!-- cannbot:related:end -->
