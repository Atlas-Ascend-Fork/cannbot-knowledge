---
type: API
title: GetTiling
description: 获取Mc2InitTiling参数和Mc2CcTiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetTiling

获取Mc2InitTiling参数和Mc2CcTiling参数。

参数：
- tiling（输出）：Tiling结构体存储的Tiling信息。

返回值：- 返回值为0，则tiling计算成功，该Tiling结构体的值可以用于后续计算。
