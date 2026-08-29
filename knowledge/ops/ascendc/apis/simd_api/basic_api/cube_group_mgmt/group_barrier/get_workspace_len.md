---
type: API
title: GetWorkspaceLen
description: 返回当前GroupBarrier所占用的Global Memory消息空间大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GetWorkspaceLen.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# GetWorkspaceLen

返回当前 GroupBarrier 所占用的 Global Memory 消息空间大小。用于在创建 GroupBarrier 前分配足够的 GM 空间。

原型：`__aicore__ inline uint32_t GetWorkspaceLen()`。无参数，返回空间大小（字节）。支持 950/a2。
