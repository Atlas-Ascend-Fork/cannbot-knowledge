---
type: Guide
title: TPipe和TQue编程范式
description: 上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。
tags: [task.lookup, topic.implementation.pipeline]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TPipe和TQue编程范式

上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。
本章将上述原理固化为可直接编码的标准化编程范式。上一章回答为什么这样设计，本章则聚焦如何按此设计编写代码。TPipe‑TQue编程范式的本质，是队列管道思想在AI Core上的工程化落地——它将流水线拆分、队列同步、内存生命周期管理、异步并行调度等复杂底层逻辑，封装为一套统一、固定的开发流程，帮助开发者快速编写规范、可流水且高性能的算子核函数。
该范式定义了算子核函数实现的标准化固定流程。开发者严格遵循此范式，无需手动编写底层同步逻辑，也不必独自处理数据依赖与时序阻塞，即可快速搭建稳定、高效的算子代码框架。
从硬件执行形态看，AI Core内部的向量单元、矩阵单元和数据搬运单元天然支持异步并行与流水线执行。TPipe‑TQue编程范式完全贴合这一硬件特性，将硬件的多级流水行为抽象为软件层面统一的数据搬入—计算—数据搬出三段式流水线开发模型。
流水并行的核心逻辑可通过示意图直观理解：完整算子任务被拆分为多个有序子阶段，不同硬件单元负责不同工序；同一数据分片需在各阶段间串行流动，以保证数据依赖合法；不同数据分片则可在不同阶段同时处理，实现流水线吞吐叠加，与经典C/C++管道程序的执行逻辑完全一致。
结合上一章的阐述可总结出：Ascend C流水线体系由两大核心模块共同支撑：
- TPipe 资源管理器：统一管理系统内存资源和用于同步的事件等；
- TQue 队列：完成Stage任务之间的同步和通信。
基于这套机制，Ascend C固化了矢量、矩阵、融合三类算子的标准化流水线编程范式。下文将结合硬件特性与工程实例逐一展开。
-   矢量编程范式
-   矩阵编程范式
-   融合算子编程范式
## 矢量编程范式
如上图所示，矢量编程范式将算子实现流程划分为三个基本任务：CopyIn、Compute和CopyOut。
- CopyIn负责数据搬入：将输入数据从Global Memory搬运到Local Memory（VECIN表示矢量计算搬入数据的存放位置），搬运完成后将数据入队；
- Compute负责矢量指令计算：从队列取出数据后，在Local Memory上执行计算，计算完成后将结果入队；
- CopyOut负责数据搬出：从队列取出计算结果，将其从Local Memory（VECOUT表示矢量计算搬出数据的存放位置）搬运回Global Memory。
上述VECIN、VECOUT均属于TPosition（逻辑位置）概念。Ascend C通过抽象的TPosition表达不同层级的物理存储，以替代直接的片上物理存储概念，实现硬件架构的隐藏。除VECIN和VECOUT外，矢量编程中还会用到VECCALC，通常在定义临时变量时使用。
从编程角度看，具体流程（如下方伪代码所示）及流程图如下：
任务间数据传递所使用的内存、事件等资源，统一由TPipe管理。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](../../../../../apis/simd_api/basic_api/resource_management/t_que/alloc_tensor.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《AllocTensor》说明从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [DeQue](../../../../../apis/simd_api/basic_api/resource_management/t_que/de_que.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《DeQue》说明从TQue取出LocalTensor供下一流水阶段处理，并与EnQue形成生产消费交接。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [DestroyWithoutPipeAll](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/destroy_without_pipe_all.md)（`explains`）：DestroyWithoutPipeAll 与《TPipe和TQue编程范式》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [EnQue](../../../../../apis/simd_api/basic_api/resource_management/t_que/en_que.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《EnQue》说明将已分配的LocalTensor放入TQue，使后续流水阶段能够按队列依赖消费该Tensor。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [FreeTensor](../../../../../apis/simd_api/basic_api/resource_management/t_que/free_tensor.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《FreeTensor》说明释放Que中的指定Tensor，需与AllocTensor配对使用。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [InitBuffer](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《InitBuffer》说明用于为TQue等队列和TBuf分配内存。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [SetFlag/WaitFlag](../../../../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《SetFlag/WaitFlag》说明核内多流水间同步指令，SetFlag在源流水前序指令完成后设置硬件标志位，WaitFlag在目的流水等待标志位并清除，标注为ISASI类别，不保证跨硬件版本兼容。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [TPipe](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe》说明TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [TPipe简介](../../../../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe_intro.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe简介》说明TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [AI Core SIMD编程模型概述](../overview.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《AI Core SIMD编程模型概述》说明SIMD并行机制是AI Core的核心算力支撑，承担了整机90%以上的计算吞吐量。因此，本章将以SIMD编程模型为核心主线，遵循「宏观架构—硬件调度—代码落地」的递进逻辑，完整覆盖SIMD算子开发全链路：阐述多AI Core集群的并行任务分发机制，拆解单AI Core内部异构计算单元的任务调度逻辑，并逐层讲解如何基于差异化的C/C++编程接口，完成算子Kernel计算逻辑的开发。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [Ascend C多层级编程接口选择参考](../../../../asc_how_to_choose_api.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《Ascend C多层级编程接口选择参考》说明欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [CppTensorProgrammingOverview](../cpp_tensor_programming/cpp_tensor_programming_overview.md)（`related`）：CppTensorProgrammingOverview 与《TPipe和TQue编程范式》的实质衔接是：C++ Tensor 编程用 Global/Local/RegTensor 覆盖 GM、UB/L1/L0、Register；静态 Tensor、Memory/Reg/Cube、kernel 与 TPipe 材料展开同一对象化数据流。
- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《FreeTensor早释使队列别名被下一轮DMA覆盖》说明fp32路径让计算张量别名队列张量时，compute完成前FreeTensor会触发UB复用，造成非确定性NaN和有限值错误。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [TQue InitBuffer 须传深度和 uint32 长度](../../../../../runbooks/compilation/tque_initbuffer_requires_depth_and_uint32_length.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TQue InitBuffer 须传深度和 uint32 长度》说明将 TBuf 的两参数 InitBuffer 写法套到 TQue 会无匹配重载；按 queue、bufferNum、uint32 len 三参数初始化后恢复构建。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TQue 输入未释放导致循环 AllocTensor 卡死》说明循环内 DeQue 的输入 Tensor 未归还 TQue，耗尽队列 buffer 后后续 AllocTensor 无进展；消费完成立即 FreeTensor。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [运行验证时AllocTensor/FreeTensor失败](../../../appendix/faq/alloc_free_tensor_failure.md)（`related`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《运行验证时AllocTensor/FreeTensor失败》说明通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [静态Tensor编程](../cpp_tensor_programming/static_tensor_programming.md)（`related`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [Memory矢量计算编程](../c_pointer_programming/memory_vector_computation.md)（`same_topic`）：Memory矢量计算编程 与《TPipe和TQue编程范式》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [TPipe-TQue编程原理介绍](tpipe_tque_principles.md)（`same_topic`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe-TQue编程原理介绍》说明Ascend C编程模型的核心架构，深度承袭了传统C/C++并发编程中队列管道(Queue Pipeline) 的经典设计理念。在通用并发编程体系中，管道模式的核心价值在于任务解耦与流程结构化：将复杂计算任务拆分为多个独立、可并行执行的处理阶段（Stage），各阶段之间通过线程安全队列完成数据传递与消息同步。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`same_topic`）：抽象硬件架构（AI Core SIMD编程） 与《TPipe和TQue编程范式》的实质衔接是：该架构页把 Scalar/Vector/Cube、Local/Global Memory 与 MTE/FixPipe 映射到 SIMD kernel；C/C++ Memory/Reg/Cube 和 TPipe 指南展开同一数据流。
<!-- cannbot:related:end -->
