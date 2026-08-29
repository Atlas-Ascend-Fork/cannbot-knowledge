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
