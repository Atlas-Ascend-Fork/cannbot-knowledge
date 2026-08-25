---
type: Guide
title: TPipe-TQue编程原理介绍
description: Ascend C编程模型的核心架构，深度承袭了传统C/C++并发编程中队列管道(Queue Pipeline) 的经典设计理念。在通用并发编程体系中，管道模式的核心价值在于任务解耦与流程结构化：将复杂计算任务拆分为多个独立、可并行执行的处理阶段（Stage），各阶段之间通过线程安全队列完成数据传递与消息同步。
tags: [task.lookup, topic.implementation.pipeline]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_principles.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TPipe-TQue编程原理介绍

## 设计思想渊源：从经典队列管道到Ascend C TPipe-TQue编程模型

Ascend C编程模型的核心架构，深度承袭了传统C/C++并发编程中**队列管道(Queue Pipeline)** 的经典设计理念。在通用并发编程体系中，管道模式的核心价值在于任务解耦与流程结构化：将复杂计算任务拆分为多个独立、可并行执行的处理阶段（Stage），各阶段之间通过线程安全队列完成数据传递与消息同步。

这种**阶段解耦、队列互联**的架构，将原本无序的异步并发控制转化为逻辑清晰、可顺序理解的数据流，从根本上规避了显式锁和复杂同步带来的心智负担，降低了并行程序的设计、调试与维护成本。

面向AI Core的异构并行计算场景，Ascend C对经典队列流水线思想进行了适配与创新，构建了专属的**TPipe-TQue并行编程模型**。该模型由三大核心要素构成：可并行执行的处理阶段（Stage）、全局资源管理、跨阶段队列同步通信。同时，Ascend C将底层硬件同步指令与片上内存生命周期管理分别封装为`EnQue`/`DeQue`和`AllocTensor`/`FreeTensor`两组标准化接口，形成了一套轻量级、高可控、标准化的异构并行编程范式。

## TPipe-TQue框架核心定义与编程原理

**TPipe**与**TQue**是支撑多Stage流水线并行运行的两大基础组件，二者职责分明、紧密协同：

- **TPipe** 作为资源管理器，统一管理系统内存资源及用于同步的事件等；
- **TQue** 作为队列，负责完成Stage任务间的同步与通信。

在TPipe-TQue模型下，完整的算子计算流程被拆分为若干独立、可并行调度的Stage，每个Stage都遵循一套标准化的四步编程范式：

1. **内存获取**：通过`AllocTensor`主动申请片上临时内存，或通过`DeQue`从上游TQue获取已就绪的数据内存。
2. **计算执行**：在获取的合法内存上完成核心计算、数据搬运或格式转换等操作。
3. **数据传递与同步**：通过`EnQue`将结果数据推入下游TQue，同时触发同步信号，唤醒等待中的下游任务。
4. **内存释放**：对于不再使用的内存，调用`FreeTensor`主动释放，并向硬件发出可覆写信号，供后续任务复用，提升片上内存利用率。

该范式将复杂的异步并行调度及硬件同步，抽象为开发者熟悉的内存管理与队列操作。以Vector矢量计算为例，这些接口会被编译器转化为底层的指令序列，形成完整的指令流水线，如下图所示：

**图1**  Vector编程范式指令队列示例

指令的生成、分发与执行遵循统一的异步流水线：

1.  **取指与解码**：标量处理单元读取算子指令序列并进行解码。
2.  **指令发射**：标量单元将解码后的指令发射到对应执行单元的指令队列。
3.  **并行执行**：各执行单元独立、并行地从各自队列中取出指令并执行。

在这种异步并行架构下，多单元、多Stage的并发执行会引入复杂的数据依赖，而这正是异构编程的核心难点。Ascend C通过两组成对的API，在底层精准植入`Set`/`Wait`硬件同步指令，以极低的性能代价解决了这一问题。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](../../../../../apis/simd_api/basic_api/resource_management/t_que/alloc_tensor.md)（`explains`）：AllocTensor 是每个 Stage 获取队列内存的起点，必须与后续 FreeTensor 配对。
- [DeQue](../../../../../apis/simd_api/basic_api/resource_management/t_que/de_que.md)（`explains`）：DeQue 获取已就绪 Tensor 并承接硬件同步，是消费 Stage 的所有权入口。
- [DestroyWithoutPipeAll](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/destroy_without_pipe_all.md)（`explains`）：DestroyWithoutPipeAll 与《TPipe-TQue编程原理介绍》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [EnQue](../../../../../apis/simd_api/basic_api/resource_management/t_que/en_que.md)（`explains`）：EnQue 发布上游完成的数据并建立跨 Stage 同步，使下游 DeQue 可安全消费。
- [FreeTensor](../../../../../apis/simd_api/basic_api/resource_management/t_que/free_tensor.md)（`explains`）：最后一个消费者完成后必须 FreeTensor，才允许底层 UB 被后续任务复用。
- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`related`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《TPipe-TQue编程原理介绍》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [Ascend C多层级编程接口选择参考](../../../../asc_how_to_choose_api.md)（`related`）：Ascend C多层级编程接口选择参考 与《TPipe-TQue编程原理介绍》的实质衔接是：概述/快速开始解释学习入口，TPipe/TQue 原理与范式对应 choice guide 的易编程层，兼容性策略说明跨代选择接口层时的稳定性成本。
- [CppTensorProgrammingOverview](../cpp_tensor_programming/cpp_tensor_programming_overview.md)（`related`）：CppTensorProgrammingOverview 与《TPipe-TQue编程原理介绍》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`related`）：TQue tensor 所有权只能 DeQue 一次 与《TPipe-TQue编程原理介绍》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [标量 S pipe 误用 TQue 导致输出全常数](../../../../../runbooks/precision/scalar_s_pipe_requires_explicit_mte_dependencies.md)（`related`）：TPipe-TQue 原理说明 EnQue/DeQue 建立生产者消费者事件；本卡提供其边界反例：事件面向 Vector 消费者，不能替代标量 S pipe 依赖。
- [Memory矢量计算编程](../c_pointer_programming/memory_vector_computation.md)（`same_topic`）：Memory矢量计算编程 与《TPipe-TQue编程原理介绍》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [TPipe和TQue编程范式](tpipe_tque_paradigm.md)（`same_topic`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe-TQue编程原理介绍》说明Ascend C编程模型的核心架构，深度承袭了传统C/C++并发编程中队列管道(Queue Pipeline) 的经典设计理念。在通用并发编程体系中，管道模式的核心价值在于任务解耦与流程结构化：将复杂计算任务拆分为多个独立、可并行执行的处理阶段（Stage），各阶段之间通过线程安全队列完成数据传递与消息同步。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《TPipe-TQue编程原理介绍》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
<!-- cannbot:related:end -->
