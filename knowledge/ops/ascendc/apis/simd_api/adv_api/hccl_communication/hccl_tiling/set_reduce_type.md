---
type: API
title: SetReduceType
description: 设置Reduce操作类型，仅对有归约操作的通信任务生效。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetReduceType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetReduceType

设置Reduce操作类型，仅对有归约操作的通信任务生效。

参数：
- reduceType（输入）：归约操作类型，仅对有归约操作的通信任务生效。uint32_t类型，取值详见表2参数说明。
- dstDataType（输入）：通信任务中输出数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。
- srcDataType（输入）：通信任务中输入数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。

返回值：- 0表示设置成功。
