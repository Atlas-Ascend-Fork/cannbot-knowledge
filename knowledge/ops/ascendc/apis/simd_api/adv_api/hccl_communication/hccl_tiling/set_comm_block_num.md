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

- [BatchWrite](../hccl_kernel/batch_write.md)（`related`）：设置参与BatchWrite通信的核数。；集合通信BatchWrite的任务下发接口，返回该任务的标识handleId给用户。；Tiling 接口生产 BatchWrite 的参与核数，Kernel 接口消费该配置下发点对点批量通信任务，形成参数生产到任务执行的直接合同。
- [SetQueueNum](set_queue_num.md)（`related`）：参与通信的核数*队列数量支持设置的取值范围为［0, 40］；设置参与BatchWrite通信的核数；两接口的乘积共同决定合法 BatchWrite 队列配置。
<!-- cannbot:related:end -->
