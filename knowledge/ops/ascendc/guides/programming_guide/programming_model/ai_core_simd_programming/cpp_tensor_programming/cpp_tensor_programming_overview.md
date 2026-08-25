---
type: Guide
title: CppTensorProgrammingOverview
description: Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cpp_tensor_programming_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# C++ Tensor编程概述

C++ Tensor编程是Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全、编译期检查的高层次编程能力。开发者通过LocalTensor、GlobalTensor、RegTensor等Tensor对象管理内存，无需直接操作指针地址，搬运计算接口直接操作Tensor对象即可完成数据流转。该路径适用于追求开发效率、类型安全、代码可维护性的算子开发场景，是习惯C++面向对象编程的开发者快速上手NPU算子开发的关键技术路径。本章旨在帮助开发者建立对C++ Tensor编程的系统化认知，理解其Tensor抽象编程范式、核心编程模型与开发方法论。
## Kernel函数
核函数在前序章节已作介绍，C++ Tensor编程在核函数定义与调用上沿用SIMD编程通用规范，无额外语法约束。
## 内存层级
AI Core采用分级存储架构，Cube矩阵计算采用「Global Memory（以下简称为GM） → L1/L0系列Buffer」两级层级服务于矩阵计算，Vector矢量计算传统架构为「Global Memory → Unified Buffer（以下简称为UB）」两级层级，而NPU架构版本3510引入寄存器后构建「GM → UB → Register」三级层级，其中GM存放输入输出数据、UB作为矢量计算中间缓存、Register位于Vector计算单元最内层直接与执行单元交互。
### Tensor内存抽象
Tensor本质是基于数组的编程抽象，而非简单的内存地址封装，通过数组方式管理内存并执行计算，更匹配SIMD硬件执行模型。其核心思想是将原始内存地址抽象为Tensor对象，实现从“地址操作”到“对象管理”的编程层次提升。
根据芯片分级存储架构，Tensor分为三类：GlobalTensor对应GM，存放算子输入/输出数据；LocalTensor对应片上内存（UB、L1 Buffer、L0A Buffer/L0B Buffer/L0C Buffer等缓冲区），承载计算过程数据；RegTensor对应寄存器，用于寄存器级矢量计算（NPU架构版本3510引入）。Tensor体系持续演进：基础Tensor仅携带数据指针和大小信息，需手动传递操作参数；扩展Tensor（Tensor API）引入Layout概念，携带Shape和Stride信息，接口可自动推导搬运长度、计算元素数等参数，大幅降低编程复杂度。该能力引入的接口统一通过AscendC::Te命名空间调用（如AscendC::Te::Mmad）。
#### 基础Tensor与扩展Tensor抽象定义
- 基础Tensor（不带Layout）仅封装数据指针与大小信息，无法表达数据的物理排布方式。开发者在执行搬运和计算时必须手动传入size/count参数、自行计算偏移与步长，面对高维张量时易出错且代码冗长。
- 扩展Tensor（Tensor API）封装Shape和Stride信息，接口自动推导操作参数，实现编译期类型安全。开发者无需关注内存布局细节，一行代码即可完成切片、搬运与计算。当前能力赋能于Cube矩阵计算，后续将逐步支持Vector矢量计算。

<!-- cannbot:related:start -->
## 相关

- [AI Core SIMD编程模型概述](../overview.md)（`related`）：AI Core SIMD编程模型概述 与《CppTensorProgrammingOverview》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [Cube矩阵计算编程](cube_matrix_computation.md)（`related`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《CppTensorProgrammingOverview》说明Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [TPipe-TQue编程原理介绍](../tpipe_tque_programming/tpipe_tque_principles.md)（`related`）：CppTensorProgrammingOverview 与《TPipe-TQue编程原理介绍》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [TPipe和TQue编程范式](../tpipe_tque_programming/tpipe_tque_paradigm.md)（`related`）：CppTensorProgrammingOverview 与《TPipe和TQue编程范式》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`related`）：CppTensorProgrammingOverview 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [核函数（AI Core SIMD编程）](../kernel_function.md)（`related`）：CppTensorProgrammingOverview 与《核函数（AI Core SIMD编程）》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [静态Tensor编程](static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《CppTensorProgrammingOverview》说明Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [MemoryVectorComputation](memory_vector_computation.md)（`same_topic`）：CppTensorProgrammingOverview 与《MemoryVectorComputation》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [Reg矢量计算编程（C++ Tensor编程）](reg_vector_computation.md)（`same_topic`）：CppTensorProgrammingOverview 与《Reg矢量计算编程（C++ Tensor编程）》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
<!-- cannbot:related:end -->
