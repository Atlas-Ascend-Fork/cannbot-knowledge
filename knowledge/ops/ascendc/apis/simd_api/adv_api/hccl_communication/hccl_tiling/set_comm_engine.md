---
type: API
title: SetCommEngine
description: 设置通信任务使用的通信引擎。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetCommEngine.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetCommEngine

设置通信任务使用的通信引擎。

参数：
- commEngine（输入）：通信引擎。uint8_t类型，该参数的取值范围请参考：HcclCommConfig中的hcclOpExpansionMode参数的取值说明。

返回值：- 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [UDMA GET size=0 污染后续 GET 致精度失败](../../../../../runbooks/precision/udma_get_size_zero_pollutes_engine_guard.md)（`exemplifies`）：污染的是具体通信 engine 状态，SetCommEngine 决定任务落在哪个引擎。
- [SetStepSize](set_step_size.md)（`same_topic`）：SetStepSize 与《SetCommEngine》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
