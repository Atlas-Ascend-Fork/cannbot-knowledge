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
