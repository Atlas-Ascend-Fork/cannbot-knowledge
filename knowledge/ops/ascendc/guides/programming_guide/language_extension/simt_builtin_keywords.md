---
type: Guide
title: SIMT BuiltIn关键字
description: 函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simt_builtin_keywords.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# SIMT BuiltIn关键字

## 函数执行空间限定符
函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。
函数执行空间限定符概览
__host__，无限定符：√：x：√：x
__aicore__：x：√：x：√
__global__：x：√：√：x
__global__修饰的函数是核函数入口，有以下使用约束：
-   函数返回类型必须为void，不能是class、struct或者union的成员函数。
-   不支持递归调用。
-   对__global__函数的调用是异步的，调用后即返回Host侧的主机线程。
-   只能被Host侧函数调用，在Device上执行。
__aicore__修饰的函数只能在Device侧执行，只能被__global__函数，或者其他__aicore__函数调用。
__host__修饰的函数只能在Host侧被调用和执行。
## 内存空间限定符
使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数执行时确定。
-   静态内存通过数组分配：
-   动态内存通过以下方式申请使用：
动态内存的实际内存大小需要在核函数启动时配置，具体内容请参考核函数配置。
## 内置常量
常量名：取值：功能
constexpr uint64_t ASC_UB_SIZE：取值由当前AI处理器决定，若该AI处理器不存在这块空间，则默认配置为0。：表示当前AI处理器架构下Unified Buffer（UB）的容量，可用于编译期获取UB资源大小。
## 内置结构体
-   dim3
dim3是内置结构体类型，由3个无符号整数组成，结构体定义为
用于指定3个不同维度的大小，三维总数为x * y * z。开发者可以通过如下方式创建dim3结构。
## 内置变量
当前提供了以下仅在Device上可用的dim3结构的内置变量：
-   gridDim
内置全局变量，只能在核函数中使用，表示整个计算任务在各个维度上分别由多少个线程块构成。
-   blockDim
内置全局变量，在核函数中可以直接使用，用于获取线程块中配置的线程的三维层次结构，即启动核函数时配置的dim3结构体实例值。blockDim.x，blockDim.y，blockDim.z分别表示线程块中三个维度的线程数。
-   blockIdx
内置全局变量，只能在核函数中使用，用于获取块索引。表示当前线程所在的线程块在整个网格中的位置坐标。

<!-- cannbot:related:start -->
## 相关

- [函数执行空间限定符](../../../apis/simt_api/simt_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`explains`）：API 页逐项定义 __host__、__global__、__aicore__ 的可调用空间，展开了 BuiltIn 指南中的入口与设备函数约束。
- [扩展语法内置变量](../../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：扩展语法内置变量 与《SIMT BuiltIn关键字》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [扩展语法内置变量](../../../apis/simt_api/simt_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：API 卡定义 blockDim/gridDim/blockIdx/threadIdx/warpSize，目标语言指南说明这些 BuiltIn 关键字在 kernel 中的索引用法与作用域。
- [SIMT语言扩展层C API](simt_language_extension_c_api.md)（`related`）：调用 SIMT 原子、Warp 和访存 C API 前，需要用 SIMT 内置关键字定义 kernel/VF 与线程执行上下文。
- [dim3 未声明：显式引入 SIMT 公共头](../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《SIMT BuiltIn关键字》明确“函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [per-core zero-out 经 grid-stride ZeroOutS](../../../runbooks/precision/per_core_zero_out_grid_stride_zeroout_simt_overshoot.md)（`related`）：per-core zero-out 经 grid-stride ZeroOutS 与《SIMT BuiltIn关键字》的实质衔接是：该故障由 ZeroOutSimt 使用 blockIdx/gridDim 的跨核 grid-stride 导致；SIMT builtin、block 数接口与 SyncAll 共同解释索引越界和回退同步要求。
- [SIMD&SIMT BuiltIn关键字](simd_simt_hybrid_builtin_keywords.md)（`same_topic`）：SIMD&SIMT BuiltIn关键字 与《SIMT BuiltIn关键字》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
<!-- cannbot:related:end -->
