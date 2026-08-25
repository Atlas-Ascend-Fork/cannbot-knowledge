---
type: API
title: TPipe
description: TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/TPipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TPipe

AscendC 统一管道管理器，是 TBuf/TQue/TBufPool 等 buffer 资源的管理入口。通过 Init/Destroy 管理生命周期，InitBuffer 为 TQue/TBuf 分配内存，InitBufPool 为 TBufPool 分配内存；AllocEventID/ReleaseEventID/FetchEventID 管理事件 ID；InitSpmBuffer/WriteSpmBuffer/ReadSpmBuffer 管理 Spm 缓冲区；GetBaseAddr 获取基地址。每个核函数通常持有一个 TPipe 实例。

<!-- cannbot:related:start -->
## 相关

- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《TPipe》说明TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [静态Tensor编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/static_tensor_programming.md)（`explains`）：《静态Tensor编程》说明在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。；《TPipe》说明TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。。二者在静态Tensor通过LocalMemAllocator或固定地址直接管理片上内存，并自行处理流水同步，与TPipe初始化模式形成明确取舍上存在可执行的直接衔接。
- [GetTPipePtr](../get_t_pipe_ptr.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《TPipe》补充：TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。
- [InitSpmBuffer](init_spm_buffer.md)（`related`）：InitSpmBuffer 与《TPipe》的实质衔接是：InitSpmBuffer 创建 GM 上的 SPM 溢出区，Read/WriteSpmBuffer 与 TPipe 生命周期共同构成初始化、访问和销毁链。
- [Destroy](destroy.md)（`same_topic`）：类型页定义 Destroy 释放的 event 和 buffer pool 生命周期。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《TPipe》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《TPipe》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
<!-- cannbot:related:end -->
