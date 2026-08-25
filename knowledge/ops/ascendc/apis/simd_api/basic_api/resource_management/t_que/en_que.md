---
type: API
title: EnQue
description: 将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/EnQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# EnQue

头文件路径为："basic_api/kernel_tpipe.h"。

将Tensor push到队列。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《EnQue》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`exemplifies`）：TQue tensor 所有权只能 DeQue 一次 与《EnQue》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [SIMD算子实现耦合模式](../../../../../guides/operator_practice/simd_operator_impl/matrix_basic_api/coupled_mode.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《EnQue》说明将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [TPipe-TQue编程原理介绍](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_principles.md)（`explains`）：EnQue 发布上游完成的数据并建立跨 Stage 同步，使下游 DeQue 可安全消费。
- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《EnQue》说明将已分配的LocalTensor放入TQue，使后续流水阶段能够按队列依赖消费该Tensor。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [基础矢量算子](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/basic_vector_operator.md)（`explains`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《EnQue》说明将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [AllocTensor](alloc_tensor.md)（`related`）：AllocTensor obtains queue-owned storage that EnQue subsequently publishes to the consumer stage.
- [DeQue](de_que.md)（`related`）：DeQue 的直接前置是把已写完的 Tensor EnQue；空队列 DeQue 被明确定义为异常，因此两者构成队列所有权交接协议。
- [GetTensorCountInQue](get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《EnQue》具体提供“将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [HasTensorInQue](has_tensor_in_que.md)（`related`）：《EnQue》明确“将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。”；它与《HasTensorInQue》的“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”在实际调用参数、数据流或结果校验上直接衔接。
- [VacantInQue](vacant_in_que.md)（`related`）：VacantInQue 返回 true 的用途就是决定是否可继续 EnQue；二者组成队列背压检查与入队动作。
- [AllocTensor](../t_que_bind/alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《EnQue》提供“将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
<!-- cannbot:related:end -->
