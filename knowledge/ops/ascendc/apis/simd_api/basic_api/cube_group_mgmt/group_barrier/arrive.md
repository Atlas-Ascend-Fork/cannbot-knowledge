---
type: API
title: Arrive（Cube核间管理）
description: 通知其他等待的AIV，本AIV已经完成其依赖的任务。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/Arrive.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# Arrive（Cube核间管理）

通知其他等待的 AIV，本 AIV 已完成其依赖的任务。与 GroupBarrier Wait 配合使用，实现 AIV 间的同步。

原型：`__aicore__ inline void Arrive()`。无参数。Arrive 组中所有 AIV 调用 Arrive 后，Wait 组的 AIV 才能继续执行。支持 950/a2。
