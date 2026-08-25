---
type: API
title: SetCommBlockNum
description: 设置参与BatchWrite通信的核数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetCommBlockNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetCommBlockNum

设置参与BatchWrite通信的核数。

本接口属于 HCCL 集合通信 Tiling 接口，用于配置多卡通信参数。

参数说明：num：输入 表示核的数量。

返回值：-   0表示设置成功。
-   非0表示设置失败。

约束：本接口仅在Atlas A3 训练系列产品/Atlas A3 推理系列产品上通信类型为HCCL_CMD_BATCH_WRITE时生效。

<!-- cannbot:related:start -->
## 相关

- [BatchWrite](../hccl_kernel/batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《SetCommBlockNum》说明设置参与BatchWrite通信的核数。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [GetQueueNum](../hccl_kernel/get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《SetCommBlockNum》说明设置参与BatchWrite通信的核数。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [SetQueueNum](set_queue_num.md)（`related`）：queue 数和通信 block 数共同决定任务并发与资源分配，需按算法配套设置。
- [GetTiling](get_tiling.md)（`same_topic`）：SetCommBlockNum 与《GetTiling》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：SetCommBlockNum 与《HCCL Tiling使用说明》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：SetCommBlockNum 与《HcclTilingData》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetOpType](set_op_type.md)（`same_topic`）：SetCommBlockNum 与《SetOpType》的实质衔接是：SetCommBlockNum 仅为 BatchWrite 设置参与核数；SetOpType选择 BatchWrite，字段写入 HcclTilingData，再由 GetTiling 生成 Kernel 通信配置。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《SetCommBlockNum》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
