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

- [BatchWrite](../hccl_kernel/batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《SetQueueNum》说明设置每个向服务端下发任务的核上的BatchWrite通信队列数量。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [GetTiling](get_tiling.md)（`related`）：SetQueueNum 的值经 GetTiling 序列化后才可被 Kernel GetQueueNum 读取。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：使用页说明 QueueNum 与算法、通信引擎等字段的调用顺序及缺省行为。
- [QueueBarrier](../hccl_kernel/queue_barrier.md)（`related`）：SetQueueNum说明设置每个向服务端下发任务的核上的BatchWrite通信队列数量。
- [SetCommBlockNum](set_comm_block_num.md)（`related`）：queue 数和通信 block 数共同决定任务并发与资源分配，需按算法配套设置。
- [GetQueueNum](../hccl_kernel/get_queue_num.md)（`same_topic`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《SetQueueNum》说明设置每个向服务端下发任务的核上的BatchWrite通信队列数量。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《SetQueueNum》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
