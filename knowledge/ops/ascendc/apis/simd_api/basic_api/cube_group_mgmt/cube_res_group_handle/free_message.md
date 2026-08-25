---
type: API
title: FreeMessage
description: 在自定义的回调函数逻辑中，完成消息处理后，调用该接口，刷新消息状态为FREE；或者待消息状态为指定状态waitState时，刷新消息状态为FREE。消息状态的介绍可以参考表2中的参数msgState。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/FreeMessage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# FreeMessage

在回调函数中完成消息处理后，刷新消息状态为 FREE。两个重载：直接刷新，或等待消息状态为指定 waitState 后再刷新。

原型：`uint16_t FreeMessage(__gm__ CubeMsgType* msg)` 和 `uint16_t FreeMessage(__gm__ CubeMsgType* msg, CubeMsgState waitState)`。参数 msg 为消息空间地址，waitState 为等待的消息状态。返回 uint16_t。支持 950/a2。
