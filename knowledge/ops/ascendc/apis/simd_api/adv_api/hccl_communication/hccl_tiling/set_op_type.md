---
type: API
title: SetOpType
description: uint32_t SetOpType(uint32_t opType)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetOpType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetOpType

设置通信任务类型。

参数：
- opType（输入）：表示通信任务类型。uint32_t类型。HCCL API提供HcclCMDType枚举定义作为该参数的取值。

返回值：- 0表示设置成功。
