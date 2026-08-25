---
type: API
title: VacantInQue
description: 查询队列是否已满，返回true表示可继续EnQue，返回false表示已满，不支持Tensor原地操作场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/VacantInQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# VacantInQue

头文件路径为："basic_api/kernel_tpipe.h"。

查询队列是否已满。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [EnQue](en_que.md)（`related`）：VacantInQue 返回 true 的用途就是决定是否可继续 EnQue；二者组成队列背压检查与入队动作。
- [GetTensorCountInQue](get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《VacantInQue》具体提供“查询队列是否已满，返回true表示可继续EnQue，返回false表示已满，不支持Tensor原地操作场景。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [HasIdleBuffer](has_idle_buffer.md)（`related`）：队列未满并不等同于存在可 AllocTensor 的空闲块；HasIdleBuffer 观测内存块资源，能区分入队容量与分配容量问题。
- [VacantInQue](../t_que_bind/vacant_in_que.md)（`related`）：TQueBind 版本提供相同的满队列判断，但作用于绑定源/目的位置、支持内存复用的队列类型，便于在更换队列模型时保持背压逻辑。
<!-- cannbot:related:end -->
