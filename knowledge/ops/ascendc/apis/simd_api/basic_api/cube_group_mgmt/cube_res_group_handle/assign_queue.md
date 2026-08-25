---
type: API
title: AssignQueue
description: AssignQueue 接口，用于 AIV 绑定 CubeResGroupHandle 中某一个消息队列的序号。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/AssignQueue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# AssignQueue

AIV 绑定 CubeResGroupHandle 中某个消息队列的序号。

原型：`__aicore__ inline void AssignQueue(uint8_t queueIdIn)`。参数 queueIdIn 为消息队列序号。支持 950/a2。
