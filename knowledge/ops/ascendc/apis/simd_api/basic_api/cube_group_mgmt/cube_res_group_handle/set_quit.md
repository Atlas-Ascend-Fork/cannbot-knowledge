---
type: API
title: SetQuit
description: 通过AllocMessage接口获取到消息空间地址后，发送退出消息，告知该消息队列对应的AIC无需处理该队列的消息。如下图，Queue5对应的AIV发了退出消息后，Block1将不再处理Queue5的任何消息。
  图1 消息队列退出示意图 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/SetQuit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# SetQuit

通过 AllocMessage 获取消息空间地址后，发送退出消息，告知对应 AIC 无需再处理该队列的消息。

原型：`__aicore__ inline void SetQuit(__gm__ CubeMsgType* msg)`。参数 msg 为消息空间地址。发送后该消息队列对应的 AIC Block 将不再处理该队列的任何消息。支持 950/a2。
