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

<!-- cannbot:related:start -->
## 相关

- [Cube核间管理Wait](wait.md)（`related`）：每个 Wait 组的 AIV 必须等对应 Arrive 组全部调用 Arrive 后才能继续，两接口共同组成一次跨核屏障握手。
- [GetWorkspaceLen](get_workspace_len.md)（`related`）：Arrive（Cube核间管理） 与《GetWorkspaceLen》的实质衔接是：GroupBarrier Arrive 必须与构造、workspace、Wait 和 usage 配套，才能形成可闭合的组内 barrier。
- [GroupBarrier](group_barrier.md)（`same_topic`）：Arrive（Cube核间管理） 与《GroupBarrier》的实质衔接是：GroupBarrier Arrive 必须与构造、workspace、Wait 和 usage 配套，才能形成可闭合的组内 barrier。
- [GroupBarrier使用说明](group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《Arrive（Cube核间管理）》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [GroupBarrier构造函数](group_barrier_constructor.md)（`same_topic`）：GroupBarrier构造函数 与《Arrive（Cube核间管理）》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
<!-- cannbot:related:end -->
