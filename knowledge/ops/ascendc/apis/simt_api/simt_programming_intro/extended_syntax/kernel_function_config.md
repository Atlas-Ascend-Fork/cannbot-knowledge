---
type: API
title: 核函数配置
description: 核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/kernel_function_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数配置

核函数是 SIMT 编程的 Device 侧入口函数，使用 __global__ 修饰符定义。返回值必须为 void，入参支持基础数据类型和指针类型（指针必须指向 Global Memory）。定义语法：__global__ void kernel_name(uint32_t* param1, float* param2, ...)。

__launch_bounds__(N)：可选配置，指定核函数启动的最大线程数，N 取值 1-2048，需 N >= blockDim.x * blockDim.y * blockDim.z，默认 1024。N 与每线程可用寄存器数对应：N=1-256 时 127 个、257-512 时 64 个、513-1024 时 32 个、1025-2048 时 16 个。建议与实际启动线程数一致。

<<<>>> 调用：执行配置含 4 参数——blocks_per_grid（dim3，线程块总数不超过 65535）、threads_per_block（dim3，需 <= __launch_bounds__ 配置）、dyn_ubuf_size（size_t，动态共享内存字节数）、stream（aclrtStream，异步执行流）。

<!-- cannbot:related:start -->
## 相关

- [核函数配置](../../simd_simt_hybrid_programming_intro/extended_syntax/kernel_function_config.md)（`related`）：核函数是 SIMT 编程的 Device 侧入口函数，使用 __global__ 修饰符定义；核函数是 SIMD 与 SIMT 混合编程的 Device 侧入口函数，使用 __global__ __vector__ 修饰。两端给出纯 SIMT 与混合编程的 Device 入口定义，迁移执行模式时必须同时调整修饰符与 GM 指针约束。
<!-- cannbot:related:end -->
