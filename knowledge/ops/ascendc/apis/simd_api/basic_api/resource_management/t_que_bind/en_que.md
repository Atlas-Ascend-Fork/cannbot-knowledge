---
type: API
title: EnQue
description: 将Tensor加入队列。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/EnQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# EnQue

头文件路径为："basic_api/kernel_tpipe.h"。

将Tensor push到队列。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ACL 507035 — 空 TQue DeQue 触发 B16 路径异常](../../../../../runbooks/compilation/tque_dequeue_requires_prior_enqueue_507035.md)（`exemplifies`）：该故障卡以未入队的 fp32 queue 被直接 DeQue 导致 507035，实证 EnQue 必须先发布对应 dtype 队列元素；补充了 API 的运行期前置条件。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：EnQue→DeQue 后还需 FreeTensor 归还 buffer；该卡证明遗漏释放会耗尽队列并阻塞后续 AllocTensor，闭合生产消费生命周期。
- [GetTensorCountInQue](../t_que/get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《EnQue》具体提供“将Tensor加入队列。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [VacantInQue](vacant_in_que.md)（`related`）：EnQue 在队列已满时不能继续提交，VacantInQue 提供入队前容量判定；二者共同定义非阻塞生产侧协议。
- [AllocTensor](alloc_tensor.md)（`same_topic`）：《AllocTensor》处理“从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。”。《EnQue》提供“将Tensor加入队列。”，其具体合同或探针直接接入AllocTensor/FreeTensor 与 EnQue/DeQue 的队列所有权、初始化和耗尽故障。
- [DeQue](de_que.md)（`same_topic`）：EnQue 把已写入的 Tensor 放入队列，DeQue 从同一队列取出可读 Tensor；前者是后者成立的直接生产者。
<!-- cannbot:related:end -->
