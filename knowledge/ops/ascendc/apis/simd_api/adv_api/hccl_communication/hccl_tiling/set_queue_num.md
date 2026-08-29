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

<!-- cannbot:related:start -->
## 相关

- [BatchWrite](../hccl_kernel/batch_write.md)（`related`）：设置每个向服务端下发任务的核上的BatchWrite通信队列数量；queueID（输入）：指定当前通信所在的队列ID，默认值为0；配置页决定 BatchWrite 调用中 queueID 的可用队列域。
- [GetQueueNum](../hccl_kernel/get_queue_num.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡“设置每个向服务端下发任务的核上的BatchWrite通信队列数量。”；Host 设置值与 Kernel 查询值构成同一 BatchWrite 队列数量合同。
- [SetCommBlockNum](set_comm_block_num.md)（`related`）：参与通信的核数*队列数量支持设置的取值范围为［0, 40］；设置参与BatchWrite通信的核数；两接口的乘积共同决定合法 BatchWrite 队列配置。
<!-- cannbot:related:end -->
