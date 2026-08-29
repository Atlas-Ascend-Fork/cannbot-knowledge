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

- [SIMT helper 误标 __simt_vf__ 导致编译失败](../../../../runbooks/compilation/simt_vf_helpers_use_simt_callee.md)（`exemplifies`）：保留被 `asc_vf_call` 直接启动的顶层函数为 `__simt_vf__`，只把它调用的辅助函数改为 `__simt_callee__`；不要改函数模板参数、返回值或业务函数体。；__simt_callee__：SIMT VF 内部辅助函数，可使用 SIMT 内置变量，返回值和入参仅支持内置数据类型及指针，只能调用 __simt_callee__ 或 __callee__ 函数。。运行手册针对 SIMT VF 辅助函数的编译失败给出 __simt_callee__ 修复，限定符卡解释该函数类型的调用关系与参数边界，是语法合同的具体排障实例。
- [SIMT 核类型推导失败 — 补 __vector__](../../../../runbooks/compilation/direct_launch_kernel_requires_vector_qualifier.md)（`exemplifies`）：SIMT VF 启动 shell 只写 `__global__ __aicore__` 而缺少 `__vector__` 函数类型属性，使 `ld.lld` 无法为模板实例化确定 AIV kernel type，因而链接失败。；主要限定符：__global__ __aicore__（算子入口，协调 VF 执行，Host 通过 <<<>>> 调用）、__aicore__（Device 侧辅助函数）、__simt_vf__（线程级并行计算任务，通过 asc_vf_call 调用）、__simd_vf__（向量级并行计算任务）、__simt_callee__（SIMT VF 子函数）、__simd_callee__（SIMD VF 子函数）、__callee__（编译期 Device 侧辅助函数）。；该链接故障是函数执行空间与 VF 调用层级配置错误的实例，API 卡提供入口、SIMT VF 与 asc_vf_call 的规范角色。
- [核函数调用未标__aicore__的纯算术辅助函数](../../../../runbooks/compilation/aicore_helper_requires_device_qualifier.md)（`exemplifies`）：在 `.asc` 中，普通 `static inline` 并不会自动获得 device 调用属性。于是 `__global__ __aicore__` 核函数看到的候选仍是 `__host__` 函数，bisheng 在重载选择阶段拒绝跨域调用。helper 的整数算术本身可在 device 上执行；补上 `__aicore__` 后，函数域与调用者一致。；主要限定符：__global__ __aicore__（算子入口，协调 VF 执行，Host 通过 <<<>>> 调用）、__aicore__（Device 侧辅助函数）、__simt_vf__（线程级并行计算任务，通过 asc_vf_call 调用）、__simd_vf__（向量级并行计算任务）、__simt_callee__（SIMT VF 子函数）、__simd_callee__（SIMD VF 子函数）、__callee__（编译期 Device 侧辅助函数）。runbook 的 host/device 调用域错误由限定符页的函数类型合同直接解释。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。；主要限定符：__global__ __aicore__（算子入口，协调 VF 执行，Host 通过 <<<>>> 调用）、__aicore__（Device 侧辅助函数）、__simt_vf__（线程级并行计算任务，通过 asc_vf_call 调用）、__simd_vf__（向量级并行计算任务）、__simt_callee__（SIMT VF 子函数）、__simd_callee__（SIMD VF 子函数）、__callee__（编译期 Device 侧辅助函数）。。两卡描述同一套 SIMD/SIMT 混合编程函数层级与执行空间限定符；指南给出调用关系，API 卡枚举限定符职责。
<!-- cannbot:related:end -->
