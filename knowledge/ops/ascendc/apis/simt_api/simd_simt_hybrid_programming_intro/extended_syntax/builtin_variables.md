---
type: API
title: 扩展语法内置变量
description: 当前提供了以下仅在Device上可用的dim3类型的内置变量：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/builtin_variables.md
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

    内置全局变量，只能在核函数中使用，用于获取块索引。表示当前线程所在的线程块在整个网格中的位置坐标。blockIdx.x的范围是0到gridDim.x - 1，blockIdx.y和blockIdx.z目前只能返回0。

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

- [dim3 未声明：显式引入 SIMT 公共头](../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：扩展语法内置变量 与《dim3 未声明：显式引入 SIMT 公共头》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [SIMD&SIMT BuiltIn关键字](../../../../guides/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md)（`explains`）：扩展语法内置变量 与《SIMD&SIMT BuiltIn关键字》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [SIMD与SIMT混合编程概述](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/overview.md)（`explains`）：扩展语法内置变量 与《SIMD与SIMT混合编程概述》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [SIMT BuiltIn关键字](../../../../guides/programming_guide/language_extension/simt_builtin_keywords.md)（`explains`）：扩展语法内置变量 与《SIMT BuiltIn关键字》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：扩展语法内置变量 与《核函数与VF函数（SIMD与SIMT混合编程）》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [编程示例（SIMD与SIMT混合编程）](../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/programming_examples.md)（`explains`）：扩展语法内置变量 与《编程示例（SIMD与SIMT混合编程）》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [内置数据类型](builtin_data_types.md)（`related`）：扩展语法内置变量 与《内置数据类型》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [扩展语法](extended_syntax.md)（`related`）：扩展语法内置变量 与《扩展语法》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [扩展语法内置变量](../../simt_programming_intro/extended_syntax/builtin_variables.md)（`related`）：扩展语法内置变量 与《扩展语法内置变量》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数配置](kernel_function_config.md)（`related`）：扩展语法内置变量 与《核函数配置》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
<!-- cannbot:related:end -->
