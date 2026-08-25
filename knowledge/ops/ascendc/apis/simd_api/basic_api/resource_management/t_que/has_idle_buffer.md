---
type: API
title: HasIdleBuffer
description: 查询Que中是否有空闲的内存块可供AllocTensor分配，不支持Tensor原地操作场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/HasIdleBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# HasIdleBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

查询Que中是否有空闲的内存块。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocTensor](alloc_tensor.md)（`related`）：HasIdleBuffer 为真表示队列仍有可分配内存块，AllocTensor 正是消耗该空闲块取得 LocalTensor 的下一步。
- [FreeTensor](free_tensor.md)（`related`）：FreeTensor 把消费完成的 Tensor 归还队列，从而恢复 HasIdleBuffer 所观察的空闲块状态。
- [GetTensorCountInQue](get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《HasIdleBuffer》具体提供“查询Que中是否有空闲的内存块可供AllocTensor分配，不支持Tensor原地操作场景。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [VacantInQue](vacant_in_que.md)（`related`）：队列未满并不等同于存在可 AllocTensor 的空闲块；HasIdleBuffer 观测内存块资源，能区分入队容量与分配容量问题。
- [HasIdleBuffer](../t_que_bind/has_idle_buffer.md)（`same_topic`）：HasIdleBuffer 与《HasIdleBuffer》的实质衔接是：HasIdleBuffer 判断队列是否可分配，需结合 Alloc/Free、EnQue/DeQue 和队列状态解释。
<!-- cannbot:related:end -->
