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

- [函数执行空间限定符](../../../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`explains`）：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。；主要限定符：__global__ __aicore__（算子入口，协调 VF 执行，Host 通过 <<<>>> 调用）、__aicore__（Device 侧辅助函数）、__simt_vf__（线程级并行计算任务，通过 asc_vf_call 调用）、__simd_vf__（向量级并行计算任务）、__simt_callee__（SIMT VF 子函数）、__simd_callee__（SIMD VF 子函数）、__callee__（编译期 Device 侧辅助函数）。。两卡描述同一套 SIMD/SIMT 混合编程函数层级与执行空间限定符；指南给出调用关系，API 卡枚举限定符职责。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](../../../../../runbooks/precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`related`）：simd vf函数：能被核函数或者__aicore__函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和__callee__函数。；AR 把跨向量块状态机留在单次 `__simd_vf__` 中，导致该调用只完成首块且同址累加无法在块间可靠提交。。指南明确 __aicore__ 经 asc_vf_call 驱动 SIMD VF，runbook 说明跨向量块循环错误地留在单次 VF 会只完成首块，支撑把 chunk 状态机移回 wrapper。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`related`）：simd vf函数：能被核函数或者__aicore__函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和__callee__函数。；放弃 RegBase/VF 路线，AddVF 改用 kernel 侧基础向量 API（`AscendC::Add` / `AscendC::Muls`，参数为 `AscendC::LocalTensor<T>` UB buffer），不再经 `asc_vf_call` / `RegTensor` / `__simd_vf__`。这是本卡推荐的 `safety_fallback` 路线。。指南定义 asc_vf_call 与 SIMD VF 的正常层级，runbook 在毕昇 exit139 场景给出完全绕过该层级并回退基础向量 API 的验证路线。
- [SIMT helper 误标 __simt_vf__ 导致编译失败](../../../../../runbooks/compilation/simt_vf_helpers_use_simt_callee.md)（`related`）：simt vf函数：使用__simt_vf__标记，能被核函数或者__aicore__函数通过asc_vf_call接口调用。simt vf函数内只能调用__simt_callee__函数和__callee__函数。；note: candidate function not viable: simt_vf function can only call simt_callee function。指南规定 SIMT VF 只能调用 __simt_callee__/__callee__，runbook 保留违反该层级时的编译诊断，构成合同到错误信号的排障链。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`related`）：simd vf函数：能被核函数或者__aicore__函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和__callee__函数。；candidate function not viable: simd_vf function can only call simd_callee function。指南规定 SIMD VF 只能调用 __simd_callee__/__callee__，runbook 给出违反该层级时的编译器原始诊断，可直接从报错回到修复合同。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`related`）：simd vf函数：能被核函数或者__aicore__函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和__callee__函数。；固定单一寻址责任：wrapper 传已按 chunk 前移的 `fAddr`/`xAddr`；callee 删除 `offset` 参数，对收到的指针直接 `LoadAlign`。调用点也删除多余实参。。指南建立 wrapper 经 asc_vf_call 进入 SIMD VF/callee 的调用层级，runbook 明确该层级中 chunk 地址只能由 wrapper 与 callee 一侧负责，避免双重偏移。
<!-- cannbot:related:end -->
