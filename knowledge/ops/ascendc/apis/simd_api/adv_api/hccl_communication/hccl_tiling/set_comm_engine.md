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
