---
type: API
title: TPipe简介
description: TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/TPipe_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TPipe简介

TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：

-   **内存资源管理**：通过TPipe的InitBuffer接口，可以为TQue和TBuf分配内存，分别用于队列的内存初始化和临时变量内存的初始化。
-   **同步事件管理**：通过TPipe的AllocEventID、ReleaseEventID等接口，可以申请和释放事件ID，用于同步控制。

<!-- cannbot:related:start -->
## 相关

- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe简介》说明TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [避免TPipe在对象内创建和初始化](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`explains`）：TPipe 介绍说明对象初始化会申请/管理同步资源和本地内存，解释把它放进频繁构造对象为何增加开销。
- [静态Tensor编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe简介》说明TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [GetTPipePtr](../get_t_pipe_ptr.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《TPipe简介》补充：TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：
- [InitSpmBuffer](init_spm_buffer.md)（`related`）：InitSpmBuffer 与《TPipe简介》的实质衔接是：InitSpmBuffer 创建 GM 上的 SPM 溢出区，Read/WriteSpmBuffer 与 TPipe 生命周期共同构成初始化、访问和销毁链。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《TPipe简介》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《TPipe简介》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe](t_pipe_constructor.md)（`same_topic`）：《TPipe简介》明确“TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：”；它与《TPipe》的“构造用来管理内存和同步的TPipe对象。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
