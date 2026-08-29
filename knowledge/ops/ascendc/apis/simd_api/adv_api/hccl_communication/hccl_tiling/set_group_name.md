---
type: API
title: SetGroupName
description: 设置通信任务所在的通信域。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetGroupName.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetGroupName

设置通信任务所在的通信域。

参数：
- groupName（输入）：当前通信任务所在的通信域。string类型，支持的最大长度为128字节。

返回值：- 0表示设置成功。
