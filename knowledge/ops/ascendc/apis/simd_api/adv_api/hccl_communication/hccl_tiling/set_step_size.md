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

<!-- cannbot:related:start -->
## 相关

- [AlltoAllV](../hccl_kernel/allto_all_v.md)（`same_topic`）：SetStepSize 与《AlltoAllV》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [Commit（HCCL集合通信）](../hccl_kernel/commit.md)（`same_topic`）：SetStepSize 与《Commit（HCCL集合通信）》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [GetTiling](get_tiling.md)（`same_topic`）：SetStepSize 与《GetTiling》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL Kernel侧接口](../hccl_kernel/hccl_kernel.md)（`same_topic`）：SetStepSize 与《HCCL Kernel侧接口》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`same_topic`）：SetStepSize 与《HCCL Tiling使用说明》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL Tiling侧接口](hccl_tiling.md)（`same_topic`）：SetStepSize 与《HCCL Tiling侧接口》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`same_topic`）：SetStepSize 与《HCCL Tiling构造函数》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL使用说明](../hccl_kernel/hccl_usage.md)（`same_topic`）：SetStepSize 与《HCCL使用说明》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HCCL集合通信Wait](../hccl_kernel/wait.md)（`same_topic`）：SetStepSize 与《HCCL集合通信Wait》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [HcclTilingData](tiling_data_struct.md)（`same_topic`）：SetStepSize 与《HcclTilingData》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [Iterate](../hccl_kernel/iterate.md)（`same_topic`）：SetStepSize 与《Iterate》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [SetAlgConfig](set_alg_config.md)（`same_topic`）：SetStepSize 与《SetAlgConfig》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [SetCommBlockNum](set_comm_block_num.md)（`same_topic`）：SetStepSize 与《SetCommBlockNum》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [SetCommEngine](set_comm_engine.md)（`same_topic`）：SetStepSize 与《SetCommEngine》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [SetOpType](set_op_type.md)（`same_topic`）：SetStepSize 与《SetOpType》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
- [SetQueueNum](set_queue_num.md)（`same_topic`）：SetStepSize 与《SetQueueNum》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
