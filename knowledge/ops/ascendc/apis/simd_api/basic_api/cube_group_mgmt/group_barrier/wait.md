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

- [Arrive（Cube核间管理）](arrive.md)（`related`）：每个 Wait 组的 AIV 必须等对应 Arrive 组全部调用 Arrive 后才能继续，两接口共同组成一次跨核屏障握手。
- [GroupBarrier](group_barrier.md)（`related`）：Wait 消费 GroupBarrier 的到达计数并阻塞至 Arrive 组完成，与 Arrive 构成屏障对。
- [GroupBarrier构造函数](group_barrier_constructor.md)（`related`）：GroupBarrier构造函数 与《Cube核间管理Wait》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GetWorkspaceLen](get_workspace_len.md)（`same_topic`）：GetWorkspaceLen 与《Cube核间管理Wait》的实质衔接是：GetWorkspaceLen 是 GroupBarrier 使用流程的第一步；返回的 GM 长度供构造函数绑定，随后由 Arrive/Wait 完成分组屏障。
- [GroupBarrier使用说明](group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《Cube核间管理Wait》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
<!-- cannbot:related:end -->
