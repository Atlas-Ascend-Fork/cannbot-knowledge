---
type: API
title: HasTensorInQue
description: 查询TQueBind队列中目前是否已有入队的Tensor。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/HasTensorInQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# HasTensorInQue

头文件路径为："basic_api/kernel_tpipe.h"。

查询Que中目前是否已有入队的Tensor。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DeQue](de_que.md)（`related`）：HasTensorInQue 是在 DeQue 前判断绑定队列是否有可取 Tensor 的安全门禁。
- [GetTensorCountInQue](../t_que/get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《HasTensorInQue》具体提供“查询TQueBind队列中目前是否已有入队的Tensor。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [GetTensorCountInQue](get_tensor_count_in_que.md)（`related`）：HasTensorInQue 用布尔值判断是否非空，GetTensorCountInQue 提供精确数量；轮询只需可用性与需要深度统计时可据此选用。
- [HasTensorInQue](../t_que/has_tensor_in_que.md)（`related`）：《HasTensorInQue》明确“查询TQueBind队列中目前是否已有入队的Tensor。”；它与《HasTensorInQue》的“查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
