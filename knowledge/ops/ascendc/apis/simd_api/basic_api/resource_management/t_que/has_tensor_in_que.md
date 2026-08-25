---
type: API
title: HasTensorInQue
description: 查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/HasTensorInQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# HasTensorInQue

头文件路径为："basic_api/kernel_tpipe.h"。

查询Que中目前是否已有入队的Tensor。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [DeQue](de_que.md)（`related`）：《DeQue》明确“将Tensor从队列中取出用于后续处理，支持non-inplace和inplace两种接口，可通过TQueBind指定源和目的位置。”；它与《HasTensorInQue》的“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”在实际调用参数、数据流或结果校验上直接衔接。
- [EnQue](en_que.md)（`related`）：《EnQue》明确“将Tensor加入队列，返回是否入队成功，可通过TQueBind指定源和目的位置实现内存复用。”；它与《HasTensorInQue》的“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetTensorCountInQue](get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《HasTensorInQue》具体提供“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [HasTensorInQue](../t_que_bind/has_tensor_in_que.md)（`related`）：《HasTensorInQue》明确“查询TQueBind队列中目前是否已有入队的Tensor。”；它与《HasTensorInQue》的“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
