---
type: Guide
title: 核函数（AI Core SIMT编程）
description: 正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/kernel_function.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 核函数

正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务。
## 核函数的定义
Ascend C支持开发者自定义核函数来扩展C++。定义核函数时，通过引入特定的函数限定符，编译器能够识别该函数需要在设备端（Device）编译，并允许其从主机端被发起调用。
核函数的定义示例如下：
定义核函数时需要遵循以下规则：
-   使用函数类型限定符__global__，标识它是一个核函数。
-   核函数必须具有void返回类型。
-   核函数参数列表需遵循函数参数列表限制。
## 核函数的调用
算子程序中的函数可以分为三类：host侧执行函数、核函数（device侧执行）、device侧执行函数（除核函数之外）。下图以Kernel直调算子开发方式为例，描述三者的调用关系：
-   host侧执行函数可以调用其它host执行函数，也就是通用C/C++编程中的函数调用；也可以通过>>调用核函数。
-   核函数可以调用除核函数之外的其它device侧执行函数。
-   device侧执行函数（除核函数之外）使用类型限定符__aicore__标识，可以调用同类的其它device侧执行函数。
Host侧通过核函数调用符>>的语法形式调用核函数，如下所示：
>>内的参数为核函数的执行配置，由4个参数决定，详细用法请参考核函数配置：
-   blocks_per_grid：dim3类型，用于指定网格（grid）的维度与规模，blocks_per_grid.x * blocks_per_grid.y * blocks_per_grid.z等于启动的线程块总数，不得大于65535。
-   threads_per_block：dim3类型，用于指定每个线程块（block）的维度与规模，threads_per_block.x * threads_per_block.y * threads_per_block.z等于每个线程块包含的线程数，需要小于等于__launch_bounds__配置。
-   dyn_ubuf_size：size_t类型，该参数指定除静态分配的内存外，本次调用为每个线程块动态分配的共享内存字节数，单位为bytes，默认设置为0。具体用法请参考共享内存中的“动态申请”方式；
-   stream：aclrtStream类型指针，指定关联的流，用于维护异步操作的执行顺序。
## Grid与Thread索引内置变量
在核函数内，Ascend C提供了内置变量来获取执行配置的参数以及线程或线程块的索引。
常用的内置索引变量说明如下：
-   threadIdx：获取当前线程在其所属线程块内的索引。

<!-- cannbot:related:start -->
## 相关

- [核函数配置](../../../../apis/simt_api/simt_programming_intro/extended_syntax/kernel_function_config.md)（`explains`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《核函数（AI Core SIMT编程）》具体提供“正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [编程模型](../../../../apis/simt_api/simt_programming_intro/programming_model.md)（`explains`）：SIMT API 编程模型卡从 API 侧定义 thread/block 执行模型，与指南的核函数声明和索引语义互相印证。
- [AI Core编译基本用法](../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：AI Core 编译说明给出如何把包含 SIMT Kernel 的源文件按目标 npu-arch 编译、链接为可执行产物，是核函数声明和 Host 启动之后的构建落地步骤。
- [核函数（AI Core SIMD编程）](../ai_core_simd_programming/kernel_function.md)（`related`）：SIMT Kernel 同样由 Host 启动但使用不同执行模型，和 SIMD Kernel 的限定符、线程抽象可对照选型。
- [编程示例（AI Core SIMT编程）](programming_examples.md)（`related`）：核函数（AI Core SIMT编程）说明正如在概述中所介绍的，能够在AI处理器（NPU）上并行执行、并由主机端（Host）发起调用的函数被称为核函数（Kernel）。核函数被设计为由大量线程（Threads）同时并行运行。每个线程都拥有独立的寄存器和栈，它们协同工作以完成海量的数据计算任务；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [AiCoreSimtProgrammingOverview](overview.md)（`same_topic`）：SIMT 编程模型概述把核函数、线程架构、内存层级、同步和原子操作组织在同一模型中。
- [ThreadArchitecture](thread_architecture.md)（`same_topic`）：线程架构说明 block/thread/warp 的索引和执行范围，决定 kernel 内如何把全局数据映射到每个 SIMT 线程。
- [抽象硬件架构（AI Core SIMT编程）](abstract_hardware_architecture.md)（`same_topic`）：SIMT 抽象硬件架构解释核函数运行在由线程块、Warp 和标量/矢量资源组成的模型上，是理解 kernel 入口并发层级的前置。
<!-- cannbot:related:end -->
