---
type: Guide
title: C语言编程概述
description: C语言编程是Ascend C SIMD编程的底层核心接口，直接映射NPU硬件指令，支持精细化控制向量、矩阵和存储等硬件资源。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/c_programming_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# C语言编程概述

C语言编程是Ascend C SIMD编程路径的底层核心接口，可直接映射NPU硬件指令，支持开发者对向量处理单元、矩阵运算单元、本地存储等硬件资源进行精细化控制。开发者可手动规划本地内存布局、管控数据流转、插入硬件流水同步指令、调整数据搬运与计算的流水并行策略，围绕计算单元、存储层次和流水同步机制来组织代码实现。该编程方式适用于对性能和可控性要求较高的算子开发场景，也是习惯C语言编程、追求极致性能的开发者充分释放NPU硬件潜能的核心技术路径。基于以上定位，下面从核函数、内存架构、同步机制、算子开发四大核心模块，逐一讲解Ascend C语言编程的核心规则与使用方法。
## Kernel函数
核函数在前序章节已作介绍。Ascend C语言编程完全沿用SIMD编程的核函数定义与调用规范，未新增额外语法约束。核函数是运行在Device侧的执行入口，所有内存读写、数据搬运、计算逻辑均在核函数内部实现。下文将首先介绍C语言编程的内存层级，这也是核函数开发的基础。
## 内存层级
AI Core采用分级存储架构，不同计算单元的编程视角有所差异：
Cube矩阵计算：采用「Global Memory → L1/L0系列Buffer」两级层级，其中L1 Buffer、L0A/L0B Buffer、L0C Buffer均服务于矩阵计算。
Vector矢量计算：传统架构采用「Global Memory → UB」两级层级；NPU架构版本3510引入寄存器后构建「Global Memory → Unified Buffer → Register」三级层级。Global Memory存放输入输出数据，Unified Buffer作为矢量计算数据中间缓存，Register位于Vector计算单元最内层，直接与矢量计算执行单元交互。
### 外部存储（Global Memory）
Global Memory是昇腾NPU的设备内存，位于AI Core外部，容量大、带宽高但访问延迟相对较长。用于存储算子的输入数据、输出结果和中间计算数据。运行在Device侧的核函数可直接访问Global Memory。Global Memory具备数据持久性：通过全局内存分配的空间，其存储的数据会一直保留，直至该内存空间被释放或应用程序终止。用户通过Runtime API完成Device侧全局内存的管理。
结合下述示例说明：Host侧通过aclrtMalloc接口分配Device侧全局内存，通过aclrtMemcpy完成Host与Device全局内存间的数据互相拷贝（Host→Device或Device→Host）；随后通过>>语法触发Device侧核函数执行运算；此外，通过aclrtMalloc分配的Device全局内存，需调用aclrtFree接口释放。有关Runtime API的更多信息与细节，可以参考《Runtime运行时API》。
此外，核函数需使用__global__函数前缀进行声明。该前缀用于标识函数在Host侧调用、Device侧执行，是Ascend C核函数的标准定义方式，确保编译器正确识别核函数入口并生成相应的硬件执行代码。

<!-- cannbot:related:start -->
## 相关

- [AI Core SIMD编程模型概述](../overview.md)（`related`）：AI Core SIMD编程模型概述 与《C语言编程概述》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [Cube矩阵计算编程](cube_matrix_computation.md)（`same_topic`）：Cube矩阵计算编程 与《C语言编程概述》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Memory矢量计算编程](memory_vector_computation.md)（`same_topic`）：Memory矢量计算编程 与《C语言编程概述》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
<!-- cannbot:related:end -->
