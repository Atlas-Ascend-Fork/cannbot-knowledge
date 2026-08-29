---
type: API
title: AllocMessage
description: AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。
  图1 AllocMessage示意图 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/AllocMessage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# AllocMessage

AIV 从消息队列申请消息空间，返回 `__gm__ CubeMsgType*` 地址。消息队列深度固定为 4，自上而下循环申请。当前空间状态为 FREE 时返回地址，否则循环等待。

原型：`template <PipeMode pipeMode = SCALAR_MODE> __aicore__ inline __gm__ CubeMsgType* AllocMessage()`。模板 pipeMode 默认 SCALAR_MODE。支持 950/a2。
