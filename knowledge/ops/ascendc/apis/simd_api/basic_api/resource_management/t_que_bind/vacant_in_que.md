---
type: API
title: VacantInQue
description: 查询TQueBind队列是否已满。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/VacantInQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# VacantInQue

头文件路径为："basic_api/kernel_tpipe.h"。

查询队列是否已满。

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [EnQue](en_que.md)（`related`）：EnQue 在队列已满时不能继续提交，VacantInQue 提供入队前容量判定；二者共同定义非阻塞生产侧协议。
- [GetTensorCountInQue](../t_que/get_tensor_count_in_que.md)（`related`）：《GetTensorCountInQue》的任务是“查询Que中已入队的Tensor数量，不支持Tensor原地操作场景。”。《VacantInQue》具体提供“查询TQueBind队列是否已满。”，它直接用于TQue 入队数量与 EnQue/DeQue/空闲状态的可观测一致性。
- [HasIdleBuffer](has_idle_buffer.md)（`related`）：VacantInQue 判断队列未满，HasIdleBuffer 判断是否有可分配缓冲，二者分别观察槽位与底层 buffer 可用性。
- [VacantInQue](../t_que/vacant_in_que.md)（`related`）：TQueBind 版本提供相同的满队列判断，但作用于绑定源/目的位置、支持内存复用的队列类型，便于在更换队列模型时保持背压逻辑。
<!-- cannbot:related:end -->
