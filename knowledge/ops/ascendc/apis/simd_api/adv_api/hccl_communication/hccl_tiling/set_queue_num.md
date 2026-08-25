---
type: API
title: SetQueueNum
description: 设置每个向服务端下发任务的核上的BatchWrite通信队列数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetQueueNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetQueueNum

设置每个向服务端下发任务的核上的BatchWrite通信队列数量。

参数：
- num（输入）：表示队列的数量。参与通信的核数*队列数量支持设置的取值范围为[0, 40]，参与通信的核数的设置请参考SetCommBlockNum。

返回值：- 0表示设置成功。
