---
type: API
title: 函数执行空间限定符
description: 函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/function_execution_space_qualifier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 函数执行空间限定符

函数执行空间限定符（Function Execution Space Qualifier）指示函数在 Host 侧还是 Device 侧执行，以及能被调用的空间范围。

三种限定符：__host__（Host 侧执行，只能被 Host 函数调用，无限定符时默认为 host）、__global__（Device 侧执行，核函数入口，只能被 Host 调用，返回类型必须为 void，不支持递归，调用为异步）、__aicore__（Device 侧执行，只能被 __global__ 或其他 __aicore__ 函数调用）。

调用关系：Host 可调用 __global__ 核函数；__global__ 可调用 __aicore__；__aicore__ 间可互相调用。

<!-- cannbot:related:start -->
## 相关

- [核函数调用未标__aicore__的纯算术辅助函数](../../../../runbooks/compilation/aicore_helper_requires_device_qualifier.md)（`exemplifies`）：The qualifier contract states that an unqualified helper is host-only and that __aicore__ functions may be called from __global__ or other __aicore__ functions.
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：函数执行空间文档说明 __global__ 是 Host 启动的 Device 入口并规定调用层级，为何纯 SIMT kernel 形参语法与 device helper 不同提供语言层边界。
- [SIMT BuiltIn关键字](../../../../guides/programming_guide/language_extension/simt_builtin_keywords.md)（`explains`）：API 页逐项定义 __host__、__global__、__aicore__ 的可调用空间，展开了 BuiltIn 指南中的入口与设备函数约束。
- [核函数配置](kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《函数执行空间限定符》具体提供“函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [函数执行空间限定符](../../simd_simt_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`same_topic`）：两张“函数执行空间限定符”卡描述同一 Host/Device 调用约束：SIMT 页定义 __host__/__global__/__aicore__，混合编程页在此基础上加入 __simt_vf__/__simd_vf__ 与 callee 层级。
<!-- cannbot:related:end -->
