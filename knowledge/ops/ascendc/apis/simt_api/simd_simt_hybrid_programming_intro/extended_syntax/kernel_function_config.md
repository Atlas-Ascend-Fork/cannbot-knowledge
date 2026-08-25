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

- [dim3 未声明：显式引入 SIMT 公共头](../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《核函数配置》明确“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；核函数配置正文说明“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [核函数（AI Core SIMD编程）](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/kernel_function.md)（`explains`）：Kernel 调用中的 numBlocks 等执行配置由配置接口展开，直接决定多份 Kernel 副本的调度。
- [ProgrammingModel](../programming_model.md)（`related`）：《核函数配置》明确“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
- [扩展语法内置变量](builtin_variables.md)（`related`）：扩展语法内置变量 与《核函数配置》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数配置](../../simt_programming_intro/extended_syntax/kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数配置》具体提供“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
