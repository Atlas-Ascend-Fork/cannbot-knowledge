---
type: API
title: Cube核间管理Wait
description: 阻塞该AIV需要等待Arrive组全部完成任务，再开始执行任务。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/Wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# Cube核间管理Wait

阻塞当前 AIV，等待 Arrive 组全部完成任务后再继续执行。与 Arrive 配合实现 AIV 间同步。

原型：`__aicore__ inline void Wait()`。无参数。Wait 组所有 AIV 调用 Wait 后阻塞，直到 Arrive 组所有 AIV 均调用 Arrive。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [Arrive（Cube核间管理）](arrive.md)（`same_topic`）：“Arrive 组中所有 AIV 调用 Arrive 后，Wait 组的 AIV 才能继续执行”定义到达侧的完成条件；“Wait 组所有 AIV 调用 Wait 后阻塞，直到 Arrive 组所有 AIV 均调用 Arrive”定义等待侧何时解除阻塞，二者组成同一 GroupBarrier 握手。
<!-- cannbot:related:end -->
