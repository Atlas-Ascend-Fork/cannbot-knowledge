---
type: Guide
title: AI Core SIMD编程模型概述
description: SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI
  Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AI Core SIMD编程模型概述

## 引言
SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。
## 异构并行计算核心模型：SPMD嵌套SIMD编程范式
昇腾NPU异构并行体系采用外层多核SPMD（Single Program Multiple Data）并行 \+ 内层单核SIMD细粒度并行的双层融合架构，是AI Core算子开发的核心理论根基。所有SIMD算子的并行逻辑、数据拆分策略、任务调度机制，均基于该编程范式实现。
多核集群层面遵循SPMD编程模型：将每个AI Core抽象成一个Block，通过内置变量block_idx作为Block索引。每个Block执行同一份算子Kernel代码，一般基于block_idx划分每个Block的数据处理范围，实现多核负载均衡与并行调度。
单核计算层面依托SIMD并行机制：单个AI Core内部基于SIMD机制实现细粒度并行，依靠硬件专用计算单元，单条指令批量完成多组同质数据的并行运算，充分挖掘单AI Core的极致算力潜力。
## 硬件底层支撑：AI Core计算单元架构与算子分类
AI Core是昇腾NPU的基础核心计算单元，采用「控制单元\+异构计算单元\+分级本地存储」的经典架构，各组件分工明确、协同联动。硬件的能力边界直接决定算子的计算形态与开发方式，下文将详细介绍AI Core核心硬件组件，以及基于硬件能力划分的标准化算子类型。
### AI Core核心硬件组件
- 标量处理单元：作为AI Core的控制中枢，主要负责地址偏移计算、指令调度与发射，统筹管控其他运算单元的指令执行流程，支撑分支、循环等各类控制流逻辑的正常运行。
- 向量处理单元Vector：遵循标准SIMD并行计算逻辑，专职执行各类向量指令，支持单指令多数据并行运算，适配元素级计算、逻辑运算、数据重组等灵活性要求高的计算场景。
- 矩阵运算单元Cube：高密度张量专用算力单元，面向矩阵乘加、高维张量卷积等算力密集型场景深度优化。硬件原生支持批量矩阵运算，典型能力为单次完成一组float16类型16×16矩阵乘法，是AI模型训练与推理场景的核心算力支撑。
- 本地存储：AI Core片内高速存储体系，用于缓存计算中间数据，规避频繁访问低速全局内存的性能损耗，降低访存延迟。其中Cube计算单元配套L1 Buffer、L0C Buffer等；Vector计算单元配套统一缓存UB（Unified Buffer）。
### 基于硬件单元的三类标准算子
根据算子核心计算逻辑对硬件单元的依赖差异，AI Core算子可划分为三大标准类型，通过专属修饰符标准化硬件资源调度规则，统一全域算子开发规范：
- 矢量类算子：核心计算逻辑完全由Vector计算单元承载，无矩阵密集运算，以元素级、逻辑类、数据重组类计算为主，适配访存密集、灵活度要求高的场景。核函数通过__vector__修饰。

<!-- cannbot:related:start -->
## 相关

- [CppTensorProgrammingOverview](cpp_tensor_programming/cpp_tensor_programming_overview.md)（`related`）：AI Core SIMD编程模型概述 与《CppTensorProgrammingOverview》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [Cube矩阵计算编程](c_pointer_programming/cube_matrix_computation.md)（`related`）：Cube矩阵计算编程 与《AI Core SIMD编程模型概述》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [C语言编程概述](c_pointer_programming/c_programming_overview.md)（`related`）：AI Core SIMD编程模型概述 与《C语言编程概述》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [Memory矢量计算编程](c_pointer_programming/memory_vector_computation.md)（`related`）：AI Core SIMD编程模型概述 与《Memory矢量计算编程》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [Reg矢量计算编程（C++ Tensor编程）](cpp_tensor_programming/reg_vector_computation.md)（`related`）：Reg矢量计算编程（C++ Tensor编程） 与《AI Core SIMD编程模型概述》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [SIMD算子实现概述](../../../operator_practice/simd_operator_impl/overview.md)（`related`）：SIMD算子实现概述 与《AI Core SIMD编程模型概述》的实质衔接是：该概述区分 Host tiling 与 Device kernel，并落到 SIMD 基础与 Matmul 实现；候选中的同名概述和 SIMD 模型是同一流程的展开而非成员枚举。
- [TPipe和TQue编程范式](tpipe_tque_programming/tpipe_tque_paradigm.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《AI Core SIMD编程模型概述》说明SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [抽象硬件架构（AI Core SIMD编程）](abstract_hardware_architecture.md)（`related`）：AI Core SIMD编程模型概述 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [核函数（AI Core SIMD编程）](kernel_function.md)（`related`）：AI Core SIMD编程模型概述 与《核函数（AI Core SIMD编程）》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [SIMD与SIMT混合编程概述](../../advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/overview.md)（`same_topic`）：AI Core SIMD编程模型概述 与《SIMD与SIMT混合编程概述》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
- [编程模型概述](../programming_model_overview.md)（`same_topic`）：AI Core SIMD编程模型概述 与《编程模型概述》的实质衔接是：该概述建立多核 SPMD 加单核 SIMD 的总体模型；Kernel/抽象硬件页展开 block 分发，C 与 C++ Tensor/Memory/Reg 路径展开不同 API 层，SIMD-SIMT 概述说明不规则控制流何时引入线程模型。
<!-- cannbot:related:end -->
