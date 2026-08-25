---
type: API
title: SetSkipBufferWindowCopy
description: 设置通信算法获取输入数据的位置。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetSkipBufferWindowCopy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetSkipBufferWindowCopy

设置通信算法获取输入数据的位置。

参数：
- skipBufferWindowCopy（输入）：表示通信算法获取输入数据的位置，uint8_t类型。

返回值：- 0表示设置成功。
