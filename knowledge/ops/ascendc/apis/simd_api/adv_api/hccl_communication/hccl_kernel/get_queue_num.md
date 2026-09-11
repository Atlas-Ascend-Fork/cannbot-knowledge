---
type: API
title: GetQueueNum
description: 获取BatchWrite通信任务的通信队列数量。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetQueueNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a3
source_headers:
- include/adv_api/hccl/hccl.h
---

# GetQueueNum

## 功能说明

获取BatchWrite通信任务的通信队列数量。

## 函数原型

```
__aicore__ inline uint16_t GetQueueNum()
```

## 参数说明

无

## 返回值说明

BatchWrite通信任务的通信队列数量。

## 约束说明

无

## 调用示例

请参见[BatchWrite的调用示例](batch_write.md#调用示例)。



<!-- cannbot:related:start -->
## 相关

- [BatchWrite](batch_write.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡要求“queueID（输入）：指定当前通信所在的队列ID，默认值为0。”；查询队列总数为 BatchWrite 选择合法 queueID 提供运行时边界。
- [SetQueueNum](../hccl_tiling/set_queue_num.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡“设置每个向服务端下发任务的核上的BatchWrite通信队列数量。”；Host 设置值与 Kernel 查询值构成同一 BatchWrite 队列数量合同。
<!-- cannbot:related:end -->
