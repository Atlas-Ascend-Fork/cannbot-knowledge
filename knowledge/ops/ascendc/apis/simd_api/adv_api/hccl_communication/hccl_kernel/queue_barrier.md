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

- [BatchWrite](batch_write.md)（`related`）：BatchWrite实现了一种点对点通信，这是一种直接传输数据的通信模式，能够同时将多份数据发送到不同的Global Memory地址上。；阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。。BatchWrite 在队列中下发多目的地址通信，QueueBarrier 则等待这些 BatchWrite 队列任务完成，是同一执行链的同步收口。
<!-- cannbot:related:end -->
