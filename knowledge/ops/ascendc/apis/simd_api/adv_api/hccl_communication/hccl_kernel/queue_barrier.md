---
type: API
title: QueueBarrier
description: 阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/QueueBarrier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a3]
---


# QueueBarrier

阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。

函数原型：
template <ScopeType type = ScopeType::ALL>
__aicore__ inline void QueueBarrier(uint16_t queueID)

参数：
- type（输入）：表示阻塞服务端的通信任务范围。类型为ScopeType，定义如下代码所示，其中参数含义为： ALL：阻塞所有队列上的通信任务 QUEUE：暂不支持 BLOCK：暂不支持 INVALID_TYPE：暂不支持 该参数的默认值为ScopeType::ALL。
- queueID（输入）：表示队列ID。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《QueueBarrier》说明阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [Finalize（HCCL集合通信）](finalize.md)（`related`）：Finalize（HCCL集合通信） 与《QueueBarrier》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《QueueBarrier》说明阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [HCCL使用说明](hccl_usage.md)（`related`）：HCCL使用说明说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。
- [SetQueueNum](../hccl_tiling/set_queue_num.md)（`related`）：SetQueueNum说明设置每个向服务端下发任务的核上的BatchWrite通信队列数量。
<!-- cannbot:related:end -->
