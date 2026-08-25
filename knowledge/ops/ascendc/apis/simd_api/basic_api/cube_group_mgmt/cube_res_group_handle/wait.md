---
type: API
title: Cube核间管理Wait
description: 在调用PostMessage或PostFakeMessage后，查询该消息是否已被AIC处理完。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/Wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# Cube核间管理Wait

调用 PostMessage 或 PostFakeMsg 后，查询消息是否已被 AIC 处理完。

原型：`template <bool sync = true> __aicore__ inline bool Wait(uint16_t offset)`。参数 offset 为 PostMessage/PostFakeMsg 返回的偏移量。模板 sync=true 时阻塞等待，false 时非阻塞查询。返回 true 表示已处理完。支持 950/a2。
