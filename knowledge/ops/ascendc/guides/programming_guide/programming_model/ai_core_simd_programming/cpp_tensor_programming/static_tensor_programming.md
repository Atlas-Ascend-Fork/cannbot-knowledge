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
