---
type: API
title: SetDebugMode
description: uint32_t SetDebugMode(uint8_t debugMode)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetDebugMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetDebugMode

设置调测模式。

参数：
- debugMode（输入）：表示选择的调测模式，uint8_t类型。参数支持的取值如下：1：关闭HCCL高阶API通信功能。/2：打印消息队列和Prepare消息执行次数等信息。/3：打印Prepare消息源数据buffer和目的数据buffer中的数据。

返回值：- 0表示设置成功。
