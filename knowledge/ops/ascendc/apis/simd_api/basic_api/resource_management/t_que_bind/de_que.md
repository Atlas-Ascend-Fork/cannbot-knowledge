---
type: API
title: DeQue
description: 将Tensor从队列中取出，用于后续处理。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/DeQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# DeQue

头文件路径为："basic_api/kernel_tpipe.h"。

将Tensor从队列中取出，用于后续处理。

约束：-   对空队列执行DeQue是一种异常行为，会在CPU调测时报错。
-   non-inplace接口，需要将TQueBind的depth模板参数设置为非零值；inplace接口，需要将TQueBind的depth模板参数设置为0。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：Runbook 通过 507035 复现说明 DeQue 前必须有匹配 EnQue，并给出空队列诊断。
- [TQue tensor 所有权只能 DeQue 一次](../../../../../runbooks/compilation/tque_tensor_ownership_single_dequeue.md)（`exemplifies`）：Runbook 说明同一队列元素不能被重复 DeQue，明确单次出队后的 Tensor 所有权边界。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：Runbook 证明 DeQue 后漏 FreeTensor 会耗尽队列资源并导致后续执行卡死。
- [FreeTensor](free_tensor.md)（`related`）：DeQue 获得的 LocalTensor 在消费结束后必须通过 FreeTensor 归还队列内存，完成所有权生命周期。
- [GetTensorCountInQue](../t_que/get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《DeQue》具体提供“将Tensor从队列中取出，用于后续处理。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [HasTensorInQue](has_tensor_in_que.md)（`related`）：HasTensorInQue 是在 DeQue 前判断绑定队列是否有可取 Tensor 的安全门禁。
- [AllocTensor](alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《DeQue》提供“将Tensor从队列中取出，用于后续处理。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [EnQue](en_que.md)（`same_topic`）：EnQue 把已写入的 Tensor 放入队列，DeQue 从同一队列取出可读 Tensor；前者是后者成立的直接生产者。
<!-- cannbot:related:end -->
