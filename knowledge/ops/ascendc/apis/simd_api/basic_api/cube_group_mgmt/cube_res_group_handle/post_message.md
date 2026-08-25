---
type: API
title: PostMessage
description: 通过AllocMessage接口获取到消息空间地址msg后，构造消息结构体CubeMsgType，发送该消息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/PostMessage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# PostMessage

通过 AllocMessage 获取消息空间地址后，构造 CubeMsgType 消息结构体并发送。

原型：`template <PipeMode pipeMode = SCALAR_MODE> __aicore__ inline uint16_t PostMessage(__gm__ CubeMsgType* msg, CubeMsgType& msgInput)`。参数 msg 为目标消息空间地址，msgInput 为待发送消息内容。返回 uint16_t offset 用于后续 Wait 查询。模板 pipeMode 默认 SCALAR_MODE。支持 950/a2。
