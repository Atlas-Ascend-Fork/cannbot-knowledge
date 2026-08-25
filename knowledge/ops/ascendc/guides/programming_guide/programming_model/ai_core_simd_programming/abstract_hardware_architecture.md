---
type: Guide
title: 抽象硬件架构（AI Core SIMD编程）
description: AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend
  C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/abstract_hardware_architecture.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 抽象硬件架构

AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。
## 概览
AI Core的抽象硬件架构可以分为计算单元、存储单元、搬运单元三类核心组件。下图以NPU架构版本2201为例，展示三类组件在AI Core中的位置关系和协同方式。
结合前述三类组件和图1，一次算子执行可以理解为三类组件协同完成数据处理的过程：Host侧下发算子任务后，算子指令序列进入Device侧的AI Core；计算单元负责控制逻辑以及标量、矢量和矩阵计算，存储单元保存输入、输出和中间数据，搬运单元负责在不同存储层级之间转移数据。
需要注意的是，上述过程并不表示各步骤完全串行执行。异构系统中存在Host侧与Device侧之间的异步并行，也存在Device内部不同执行单元之间的流水化并行。后续章节将分别介绍计算单元、存储单元和搬运单元的具体组成，并进一步说明异步执行与同步机制之间的关系。
## 计算单元
AI Core中的计算单元主要包括Scalar、Vector和Cube三类。
计算单元
组件名称：组件功能：对应编程概念
Scalar：执行地址计算、循环控制等标量计算工作，并把矢量计算、矩阵计算、数据搬运、同步指令发射给对应单元执行。：核函数中的控制逻辑、同步控制API。
Vector：负责执行矢量运算。：矢量计算API、矢量类算子。
Cube：负责执行矩阵运算。：矩阵计算API、矩阵类算子。
## 存储单元和搬运单元
存储单元可以从使用位置上分为Local Memory和Global Memory。
-   Local Memory：AI Core片内存储，用于暂存从Global Memory搬入的数据分片，并保存计算输出和中间结果。这些数据可供Vector、Cube等计算单元高效访问，继续参与片内计算，或通过搬运单元搬出到Global Memory。Local Memory包含面向不同编程方式和计算单元的片内资源，如图2所示。
-   Global Memory：Device侧全局存储，是Local Memory中数据搬入和搬出的主要来源或目的位置。
DMA（Direct Memory Access）搬运单元负责数据搬运，包括Global Memory和Local Memory之间的数据搬入、搬出，以及不同层级Local Memory之间的数据流转。常见搬运单元包括MTE1、MTE2、MTE3和FixPipe，具体介绍请参考搬运单元。
## 执行流程与同步机制
理解抽象硬件架构时，还需要关注不同单元如何协同完成一次数据块处理。可以从异步指令流、同步信号流、计算数据流三个视角理解：
-   异步指令流：表示Scalar计算单元对其他执行单元的任务发射关系，而不是完整指令执行流程。

<!-- cannbot:related:start -->
## 相关

- [AI Core SIMD编程模型概述](overview.md)（`related`）：AI Core SIMD编程模型概述 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [CppTensorProgrammingOverview](cpp_tensor_programming/cpp_tensor_programming_overview.md)（`related`）：CppTensorProgrammingOverview 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [Cube矩阵计算编程](c_pointer_programming/cube_matrix_computation.md)（`related`）：Cube矩阵计算编程 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube矩阵计算编程](cpp_tensor_programming/cube_matrix_computation.md)（`related`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《抽象硬件架构（AI Core SIMD编程）》说明AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [Reg矢量计算编程（C++ Tensor编程）](cpp_tensor_programming/reg_vector_computation.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [静态Tensor编程](cpp_tensor_programming/static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《抽象硬件架构（AI Core SIMD编程）》说明AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [MemoryVectorComputation](cpp_tensor_programming/memory_vector_computation.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《MemoryVectorComputation》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [Memory矢量计算编程](c_pointer_programming/memory_vector_computation.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《Memory矢量计算编程》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [Reg矢量计算编程（C指针编程）](c_pointer_programming/reg_vector_computation.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《Reg矢量计算编程（C指针编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [TPipe-TQue编程原理介绍](tpipe_tque_programming/tpipe_tque_principles.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《TPipe-TQue编程原理介绍》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [TPipe和TQue编程范式](tpipe_tque_programming/tpipe_tque_paradigm.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《TPipe和TQue编程范式》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [基本架构（硬件实现）](../../advanced_programming/hardware_implementation/basic_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《基本架构（硬件实现）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [抽象硬件架构（AI Core SIMT编程）](../ai_core_simt_programming/abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《抽象硬件架构（AI Core SIMT编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [抽象硬件架构（SIMD与SIMT混合编程）](../../advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《抽象硬件架构（SIMD与SIMT混合编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
- [核函数（AI Core SIMD编程）](kernel_function.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《核函数（AI Core SIMD编程）》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
<!-- cannbot:related:end -->
