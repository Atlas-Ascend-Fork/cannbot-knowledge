---
type: API
title: AllocTensor
description: 从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/AllocTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AllocTensor

头文件路径为："basic_api/kernel_tpipe.h"。

从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。

约束：-   同一个TPosition上的所有Queue，连续调用AllocTensor接口申请的Tensor数量，根据AI处理器型号的不同，有数量约束。申请Buffer时，需要满足该约束。

    - Ascend 950PR/Ascend 950DT不超过8个。

    - Atlas A3 训练系列产品/Atlas A3 推理系列产品不超过8个。

    - Atlas A2 训练系列产品/Atlas A2 推理系列产品不超过8个。

    - Atlas 200I/500 A2 推理产品不超过8个。

    - Atlas 推理系列产品AI Core不超过8个。

    - Atlas 推理系列产品Vector Core不超过8个。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：ACL 507035 — 空 TQue DeQue 触发 B16 路径异常 与《AllocTensor》的实质衔接是：空队列 DeQue 违反 AllocTensor→EnQue→DeQue→FreeTensor 的所有权链；相关失败卡覆盖重复 DeQue、早释、未释放、InitBuffer 参数和验证报错，Sin/Cos 是该 B16 分支中实际触发计算。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`exemplifies`）：TQue tensor 所有权只能 DeQue 一次 与《AllocTensor》的实质衔接是：TQue 元素必须严格 Alloc→EnQue→DeQue→Free 且只由一个消费者出队；相关 API、生命周期指南和失败卡覆盖临时值、早释、空队列及跨函数交接。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：AllocTensor 消费队列空闲块，若前次 DeQue 未 Free 则后续分配无可用块；这是挂死的直接资源机制。
- [TPipe-TQue编程原理介绍](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_principles.md)（`explains`）：AllocTensor 是每个 Stage 获取队列内存的起点，必须与后续 FreeTensor 配对。
- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《AllocTensor》说明从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [运行验证时AllocTensor/FreeTensor失败](../../../../../guides/programming_guide/appendix/faq/alloc_free_tensor_failure.md)（`explains`）：《运行验证时AllocTensor/FreeTensor失败》给出“通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下：”；该约束/探针可直接复现、解释或前置验证《AllocTensor》中的“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”。
- [EnQue](en_que.md)（`related`）：AllocTensor obtains queue-owned storage that EnQue subsequently publishes to the consumer stage.
- [FreeTensor](free_tensor.md)（`related`）：《FreeTensor》明确“释放Que中的指定Tensor，需与AllocTensor配对使用。”；它与《AllocTensor》的“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [HasIdleBuffer](has_idle_buffer.md)（`related`）：HasIdleBuffer 为真表示队列仍有可分配内存块，AllocTensor 正是消耗该空闲块取得 LocalTensor 的下一步。
- [InitBuffer](../t_pipe/init_buffer.md)（`related`）：《InitBuffer》给出“用于为TQue等队列和TBuf分配内存。”；该约束/探针可直接复现、解释或前置验证《AllocTensor》中的“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”。
- [AllocTensor](../t_que_bind/alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《AllocTensor》提供“从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
<!-- cannbot:related:end -->
