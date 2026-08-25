---
type: API
title: SetStepSize
description: 设置细粒度通信时，通信算法的步长，即设置细粒度通信时，一次子通信任务执行或准备执行的通信算法的步骤数。例如，图1使用pairwise算法的AlltoAllV通信步骤示意图中，该细粒度通信场景下，AlltoAllV通信任务的通信步长为1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetStepSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetStepSize

设置[细粒度通信](../hccl_kernel/iterate.md)时，通信算法的步长，即设置细粒度通信时，一次子通信任务执行或准备执行的通信算法的步骤数。例如，[图1使用pairwise算法的AlltoAllV通信步骤示意图](../hccl_kernel/iterate.md)中，该细粒度通信场景下，AlltoAllV通信任务的通信步长为1。

参数：
- stepSize（输入）：设置细粒度通信时，每次通信的步长。0表示当前非细粒度通信。

返回值：- 0表示设置成功。
