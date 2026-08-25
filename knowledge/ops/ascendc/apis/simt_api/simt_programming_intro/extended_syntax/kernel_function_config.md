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

- [dim3 未声明：显式引入 SIMT 公共头](../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《dim3 未声明：显式引入 SIMT 公共头》具体提供“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](../../../../runbooks/compilation/pure_simt_parameters_do_not_use_gm_qualifier.md)（`exemplifies`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《纯 SIMT kernel 形参 __gm__ 导致编译失败》具体提供“CANN 9.0.1 的纯 SIMT 编译模式会把 __gm__ 展开为 device attribute；kernel 形参应使用普通类型化指针。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [ThreadArchitecture](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/thread_architecture.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《ThreadArchitecture》具体提供“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数与VF函数（SIMD与SIMT混合编程）》具体提供“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将介绍整体函数类型和调用关系，再详细展开每种函数的定义、调用语法及约束。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [核函数（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/kernel_function.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数（AI Core SIMT编程）》具体提供“正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [SIMT编程简介](../simt_programming_intro.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《SIMT编程简介》具体提供“SIMT编程简介，包含编程模型、扩展语法和API列表的导航入口。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [内存空间限定符](memory_space_qualifier.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《内存空间限定符》具体提供“在SIMT编程中使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数启动时确定。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [函数执行空间限定符](function_execution_space_qualifier.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《函数执行空间限定符》具体提供“函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [扩展语法](extended_syntax.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《扩展语法》具体提供“扩展语法索引，包含函数执行空间限定符、内存空间限定符、内置类型、变量、宏与核函数配置。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [扩展语法内置变量](builtin_variables.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《扩展语法内置变量》具体提供“当前提供了以下仅在Device上可用的dim3类型的内置变量：”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [核函数配置](../../simd_simt_hybrid_programming_intro/extended_syntax/kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数配置》具体提供“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
