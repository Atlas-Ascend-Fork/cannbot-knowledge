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

<!-- cannbot:related:start -->
## 相关

- [SimdSimtHybridProgrammingIntro](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/simd_simt_hybrid_programming_intro.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SimdSimtHybridProgrammingIntro正文说明“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [VF调用](../../../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；VF调用正文说明“Reg矢量计算VF调用接口索引页，包含asc_vf_call”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [asc_vf_call](../../../../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；asc_vf_call正文说明“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [函数执行空间限定符](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；函数执行空间限定符正文说明“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [扩展语法内置变量](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：扩展语法内置变量 与《核函数与VF函数（SIMD与SIMT混合编程）》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数配置](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/kernel_function_config.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；核函数配置正文说明“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [核函数配置](../../../../../apis/simt_api/simt_programming_intro/extended_syntax/kernel_function_config.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数与VF函数（SIMD与SIMT混合编程）》具体提供“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](../../../../../runbooks/precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；AR 跨块循环放在 __simd_vf__ 只执行首块正文说明“Ascend950 Reg kernel 把 AR 跨向量块状态机留在单次 __simd_vf__ 中时只完成首块；将循环上移至 __aicore__ wrapper，并在同址读改写调用之间加入 Vector barrier”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃正文说明“Ascend950/arch35/CANN 9.1.0 下用 __simd_vf__ + AscendC::Reg::* + asc_vf_call 实现 VF 函数，bisheng 前端 SIGSEGV（exit 139）或后端 "Do not know how to scal”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [SIMD&SIMT BuiltIn关键字](../../../language_extension/simd_simt_hybrid_builtin_keywords.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《核函数与VF函数（SIMD与SIMT混合编程）》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [SIMD与SIMT混合算子性能优化概述](../../../../operator_practice/simd_simt_hybrid_optimization/overview.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMD与SIMT混合算子性能优化概述正文说明“AI Core上SIMD与SIMT混合编程结合了SIMD多数据并行计算能力与SIMT离散访存、复杂分支处理能力，可以在同一算子中以Vector Function（VF）为基本调度单位灵活组织SIMD和SIMT执行逻辑。SIMD编程适合处理连续、规整的向量或矩阵计算，SIMT编程适”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [SIMT VF 栈数组动态索引致输出全零](../../../../../runbooks/precision/simt_vf.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMT VF 栈数组动态索引致输出全零正文说明“__simt_vf__ 计算函数内声明栈分配固定大小数组（如 int32_t rowPtrStart[32]）并用运行期变量下标动态索引（rowPtrStart[localR]）时，SIMT 编译器生成错误代码——数组读写未落在预期栈位置，Pass1 marker 与 Pass2”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [SIMT __ubuf__ 静态数组 UB 占用不随分支释放](../../../../../runbooks/compilation/simt_ubuf_ub.md)（`related`）：《SIMT __ubuf__ 静态数组 UB 占用不随分支释放》说明SIMT kernel 的 __ubuf__ 静态数组是编译期分配、生命周期绑所在函数栈的 UB 资源，运行时分支只控制是否解引用、不控制是否占用；把“需要该数组”与“不需要该数组”两条路径塞进同一函数，会令不解引用的路径也白白占住 UB。给出按解引用关系拆函数的判别方法。；《核函数与VF函数（SIMD与SIMT混合编程）》说明SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。。二者在SIMT静态__ubuf__数组按函数栈常驻，地址空间限定、UB预算及TBuf管理方案直接决定如何拆函数或改为受管内存上存在可执行的直接衔接。
- [SIMT helper 误标 __simt_vf__ 导致编译失败](../../../../../runbooks/compilation/simt_vf_helpers_use_simt_callee.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMT helper 误标 __simt_vf__ 导致编译失败正文说明“SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [__simd_vf__ if constexpr 致 hoisted 报错](../../../../../runbooks/compilation/simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《核函数与VF函数（SIMD与SIMT混合编程）》说明SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；simd_vf 互调导致 helper 编译失败正文说明“__simd_vf__ 函数不能直接调用另一个 __simd_vf__ helper；把被调 helper 标为 __simd_callee__ 后调用约束诊断消失”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；分块 wrapper 与 VF callee 不可重复叠加 offset正文说明“asc_vf_call 已传入按 chunk 前移的 UB 指针时，VF callee 再加同一 offset 会从第二块开始按双倍偏移读错数据”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [带主元 Thomas 求解器 SIMT 直访 GM kernel](../../../../../runbooks/compilation/gtsv2_partial_pivoting_thomas_simt_direct_gm_kernel.md)（`related`）：函数层级指南系统定义 kernel、__simt_vf__、__simt_callee__ 与 asc_vf_call 调用关系，解释 Gtsv2 的入口和 helper 结构。
- [技术附录函数](../../../../technical_appendix/cpp_standard_support/syntax_restrictions/functions.md)（`related`）：两卡共同描述 kernel、SIMD VF、SIMT VF 与 callee 的调用图；focal 补充参数/POD/地址空间限制，目标提供调用者与被调用者层级。
- [核函数（AI Core SIMD编程）](../../../programming_model/ai_core_simd_programming/kernel_function.md)（`related`）：混合编程指南补充 Kernel 与 VF 的调用边界，可用于含 __simt_vf__ 或 __simd_vf__ 辅助函数的实现。
- [编程示例（SIMD与SIMT混合编程）](programming_examples.md)（`related`）：“编程示例（SIMD与SIMT混合编程）”定义：本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。；“核函数与VF函数（SIMD与SIMT混合编程）”定义：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。。实质衔接：gather&adds 样例同时依赖 kernel/VF 调用层级、GM/UB/私有内存边界和混合模式选择；算子实现页把示例语法落到工程流程。
- [SIMD与SIMT混合编程概述](overview.md)（`same_topic`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMD与SIMT混合编程概述正文说明“为提升向量计算在复杂控制流、离散访存等场景下的编程灵活性，在SIMD与SIMT深度融合的混合编程架构中：矩阵计算单元延续SIMD设计，向量计算单元则在SIMD基础上引入SIMT能力。这一设计确立了以SIMD为主、SIMT为辅的混合编程模型”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [内存层级（SIMD与SIMT混合编程）](memory_hierarchy.md)（`same_topic`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；内存层级（SIMD与SIMT混合编程）正文说明“在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量最小，访问效率最高”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [基础知识（SIMD与SIMT混合算子实现）](../../../../operator_practice/simd_simt_hybrid_operator_impl/basics.md)（`same_topic`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；基础知识（SIMD与SIMT混合算子实现）正文说明“本节内容为使用Reg矢量计算API和SIMT API进行SIMD与SIMT混合编程的指导”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [算子实现（SIMD与SIMT混合算子实现）](../../../../operator_practice/simd_simt_hybrid_operator_impl/operator_impl.md)（`same_topic`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；算子实现（SIMD与SIMT混合算子实现）正文说明“以下内容以gather & adds算子为例，介绍SIMD与SIMT混合算子的实现过程。完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样例”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
<!-- cannbot:related:end -->
