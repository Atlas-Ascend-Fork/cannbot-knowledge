---
type: API
title: GetQueueNum
description: 获取BatchWrite通信任务的通信队列数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetQueueNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a3]
---

# GetQueueNum

获取BatchWrite通信任务的通信队列数量。

函数原型：__aicore__ inline uint16_t GetQueueNum()

返回值：BatchWrite通信任务的通信队列数量。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [BatchWrite](batch_write.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡要求“queueID（输入）：指定当前通信所在的队列ID，默认值为0。”；查询队列总数为 BatchWrite 选择合法 queueID 提供运行时边界。
- [SetQueueNum](../hccl_tiling/set_queue_num.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡“设置每个向服务端下发任务的核上的BatchWrite通信队列数量。”；Host 设置值与 Kernel 查询值构成同一 BatchWrite 队列数量合同。
<!-- cannbot:related:end -->
