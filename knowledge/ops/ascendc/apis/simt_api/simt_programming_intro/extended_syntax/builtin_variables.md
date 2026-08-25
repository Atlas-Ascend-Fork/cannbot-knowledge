---
type: API
title: 扩展语法内置变量
description: 当前提供了以下仅在Device上可用的dim3类型的内置变量：
tags: [task.lookup, topic.implementation.api_layer.simt_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/builtin_variables.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 扩展语法内置变量

当前提供了以下仅在Device上可用的dim3类型的内置变量：

-   blockDim

    内置全局变量，在核函数中可以直接使用，用于获取线程块中配置的线程的三维层次结构。blockDim.x，blockDim.y，blockDim.z分别表示线程块中三个维度的线程数。

-   gridDim

    内置全局变量，只能在核函数中使用，表示整个计算任务在各个维度上分别由多少个线程块构成。

-   blockIdx

    内置全局变量，只能在核函数中使用，用于获取块索引，表示当前线程所在的线程块在整个网格中的位置坐标。

-   threadIdx

    内置全局变量，在核函数中可以直接使用，用于获取当前线程在线程块内部的索引。threadIdx.x，threadIdx.y，threadIdx.z分别表示当前线程在3个维度的索引，threadIdx.x的范围为[0, blockDim.x)，threadIdx.y的范围为[0, blockDim.y)，threadIdx.z的范围为[0, blockDim.z)。线程块内线程的索引计算方式如下：

    -   对于一维线程块，线程块内线程的索引为threadIdx.x。
    -   对于二维线程块，线程块内线程的索引为(threadIdx.x + threadIdx.y * blockDim.x)。
    -   对于三维线程块，线程块内线程的索引为(threadIdx.x + threadIdx.y * blockDim.x + threadIdx.z * blockDim.x * blockDim.y)。

当前提供了以下仅在Device上可用的int类型的内置变量：

-   warpSize

    const int32_t类型变量，表示一个线程束（Warp）中的线程数量，当前为固定值32。

<!-- cannbot:related:start -->
## 相关

- [Hello World](../../../../guides/getting_started/quick_start/simt_programming/hello_world.md)（`explains`）：SIMT Hello World 打印核号/线程上下文，内置变量卡给出 blockIdx、threadIdx 等执行坐标，是理解样例每个执行实例输出来源的直接前置。
- [SIMT BuiltIn关键字](../../../../guides/programming_guide/language_extension/simt_builtin_keywords.md)（`explains`）：API 卡定义 blockDim/gridDim/blockIdx/threadIdx/warpSize，目标语言指南说明这些 BuiltIn 关键字在 kernel 中的索引用法与作用域。
- [ThreadArchitecture](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/thread_architecture.md)（`explains`）：内置变量是实现线程架构身份映射的实际接口，直接提供 gridDim、blockDim、blockIdx、threadIdx。
- [扩展语法内置变量](../../simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`related`）：扩展语法内置变量 与《扩展语法内置变量》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数配置](kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《扩展语法内置变量》具体提供“当前提供了以下仅在Device上可用的dim3类型的内置变量：”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
