---
type: API
title: SetSkipLocalRankCopy
description: 设置本卡的通信算法的计算结果是否输出到目的数据buffer地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetSkipLocalRankCopy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetSkipLocalRankCopy

设置本卡的通信算法的计算结果是否输出到目的数据buffer地址。

参数：
- skipLocalRankCopy（输入）：本卡的通信算法的计算结果是否输出到recvBuf（目的数据buffer地址）。

返回值：- 0表示设置成功。
