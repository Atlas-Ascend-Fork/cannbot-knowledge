---
type: API
title: 核函数配置
description: 核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/kernel_function_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数配置

核函数是 SIMD 与 SIMT 混合编程的 Device 侧入口函数，使用 __global__ __vector__ 修饰。返回值必须为 void，入参支持指针类型（需 __gm__ 修饰）和内置数据类型。定义语法：__global__ __vector__ void kernel_name(__gm__ type* param1, ...)。

__launch_bounds__(N)：可选配置，指定 SIMT VF 启动最大线程数，N 取值 1-2048，默认 1024。N 与每线程寄存器数对应：1-256→127、257-512→64、513-1024→32、1025-2048→16。

<<<>>> 调用：参数为 block_num（uint32_t，[1,65535]）、dyn_ub_size（uint32_t，动态内存字节数）、stream（aclrtStream）。gridDim 为一维（gridDim.x=block_num，y/z 均为 1）。

asc_vf_call：启动 SIMT VF 子任务。原型 template <auto funcPtr, typename... Args> __aicore__ inline void asc_vf_call(dim3 threadNums, Args&&... args)。threadNums 指定线程块内线程数（x*y*z <= 2048，建议 32 倍数），args 传递实参。

<!-- cannbot:related:start -->
## 相关

- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：核函数是 SIMD 与 SIMT 混合编程的 Device 侧入口函数，使用 __global__ __vector__ 修饰。返回值必须为 void，入参支持指针类型（需 __gm__ 修饰）和内置数据类型。；CANN 9.0.1 的纯 SIMT 编译前端把 `__gm__` 展开成变量级 `__attribute__((device))`，该 attribute 不能修饰 `__global__` 函数的非静态形参。；API 规定混合入口需 __gm__，runbook 给出纯 SIMT 编译模式必须移除该限定的具体编译原因。
- [核函数配置](../../simt_programming_intro/extended_syntax/kernel_function_config.md)（`related`）：核函数是 SIMT 编程的 Device 侧入口函数，使用 __global__ 修饰符定义；核函数是 SIMD 与 SIMT 混合编程的 Device 侧入口函数，使用 __global__ __vector__ 修饰。两端给出纯 SIMT 与混合编程的 Device 入口定义，迁移执行模式时必须同时调整修饰符与 GM 指针约束。
<!-- cannbot:related:end -->
