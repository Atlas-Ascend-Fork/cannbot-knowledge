---
type: Guide
title: 静态Tensor编程
description: 在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 静态Tensor编程

在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。
基于以上原因，Ascend C提供了静态Tensor编程方式，相比基于Pipe的编程方式，这种方式避免了TPipe内存管理初始化过程（约数百纳秒），从而减少了运行时开销，更有助于开发者实现极致性能。通过直接构造指定地址和存储位置的LocalTensor，并将其传递给计算、搬运等API进行编程，提供了更高的灵活性。然而，这种编程方式也带来了更高的开发复杂性，需要开发者自行管理DoubleBuffer和同步流水，并且只能使用Ascend C的基础API，而非全部功能。
两种编程方式的对比如下：
## 编程范式
-   AI Core包括多种内存单元，比如用于矢量计算的Unified Buffer和用于矩阵计算的L1 Buffer、L0A Buffer、L0B Buffer、L0C Buffer等内存资源。开发者完全自主管理AI Core上的所有内存资源，创建Tensor分配地址时管理内存大小、内存复用关系并确保分配的地址有效性。
-   AI Core包括多种指令流水类型，比如Vector/Cube/Scalar计算流水，MTE1、MTE2、MTE3搬运流水等，每条流水并行执行，它们之间的依赖关系通过同步事件来协调。开发者调用Ascend C提供的搬运或者计算类API编写算子并根据数据依赖关系插入对应的同步事件，以达成最优性能。
下图是一个典型矢量算子的示意图，开发者首先根据业务计算量进行数据分块处理，之后根据核内的数据依赖关系完成同步事件的插入：
## 内存管理
静态Tensor编程方式下，开发者可以使用两种方式创建Tensor：
-   通过LocalMemAllocator指定硬件位置进行Tensor分配。
LocalMemAllocator是一种线性内存分配器，开发者可以调用Alloc方法进行内存分配，地址分配从0开始，根据调用次序依次向后进行线性分配，LocalMemAllocator只是一个简单的线性分配器，并不提供内存释放以及其它内存管理的能力。在不关注Bank冲突场景或者算子初始功能开发时，可以使用LocalMemAllocator简化算子编写，在后续性能优化时切换到使用LocalTensor进行地址分配的方式。
-   通过LocalTensor构造函数创建Tensor，极致性能场景推荐使用此方式。
开发者可以使用LocalTensor构造函数直接指定内存地址，实现内存的完全自主管理（本质上无需申请和释放内存）。使用时，需根据需求合理指定地址（不超过物理存储上限），并在保证功能正确的前提下进行内存复用。如果需要通过规避Bank冲突或者复用内存来获得极致性能时，推荐使用该方式。
## 同步管理
根据前文介绍的硬件架构，AI Core内部异步并行计算存在多条流水（包括矢量计算、矩阵计算、数据搬入、数据搬出等），多条流水之间存在数据依赖时，需要插入对应的同步事件。

<!-- cannbot:related:start -->
## 相关

- [LocalMemAllocator](../../../../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《LocalMemAllocator》说明LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [LocalMemAllocator简介](../../../../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator_intro.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《LocalMemAllocator简介》说明LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [TPipe](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe》说明TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [TPipe简介](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe_intro.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe简介》说明TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [CppTensorProgrammingOverview](cpp_tensor_programming_overview.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《CppTensorProgrammingOverview》说明Ascend C SIMD编程路径的基础编程接口，基于Tensor对象抽象封装内存地址，提供类型安全和编译期检查的高层次编程能力。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [Cube矩阵计算编程](cube_matrix_computation.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [MemoryVectorComputation](memory_vector_computation.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《MemoryVectorComputation》说明基于Unified Buffer的矢量计算编程方式，是Ascend C最基础、最通用的矢量编程接口，支持数据搬入、计算、搬出三步流程。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [Reg矢量计算编程（C++ Tensor编程）](reg_vector_computation.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《Reg矢量计算编程（C++ Tensor编程）》说明本文介绍如何使用基础API（C++模板接口）编写Reg矢量计算代码。基础API与Reg矢量计算编程（语言扩展C API）描述的是同一套Reg矢量硬件能力，功能语义一致，主要区别在于API命名、类型表达和可配置参数的表达方式。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [TPipe和TQue编程范式](../tpipe_tque_programming/tpipe_tque_paradigm.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《抽象硬件架构（AI Core SIMD编程）》说明AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细的硬件架构信息或者原理，请参考硬件实现。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [避免TPipe在对象内创建和初始化](../../../../operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《避免TPipe在对象内创建和初始化》说明【编译器背景知识】创建类对象时，会分配内存空间，用于存储类中的相关成员变量或函数。当类中变量需要参与计算时，变量值从内存被加载到寄存器，计算完成后，变量从寄存器存储回内存。Scalar常量折叠和常量传播是编译器编译时的优化方式，优化前编译器会判断变量是否只初始化过一次或只赋值过一次，若满足此编译优化的前提条件，变量值将会尽量驻留在寄存器中，从而在后续使用变量时，将减少读取内存的操作，提升运行性能。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
<!-- cannbot:related:end -->
