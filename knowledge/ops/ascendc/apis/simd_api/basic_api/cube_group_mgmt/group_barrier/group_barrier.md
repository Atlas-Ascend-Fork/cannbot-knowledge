---
type: API
title: GroupBarrier
description: GroupBarrier 接口集，提供分组同步能力，含构造函数、Arrive、Wait、GetWorkspaceLen 等接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GroupBarrier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# GroupBarrier

Cube 资源分组的同步屏障接口，用于在分组内多个 Cube 任务间实现到达-等待同步。Arrive 表示当前任务到达屏障，Wait 阻塞等待分组内所有任务到达；GetWorkspaceLen 用于获取屏障所需 workspace 长度。需配合 CubeResGroupHandle 使用，构造时绑定目标分组与 workspace，使用前应阅读使用说明确认 workspace 分配方式。

<!-- cannbot:related:start -->
## 相关

- [Cube核间管理Wait](wait.md)（`related`）：Wait 消费 GroupBarrier 的到达计数并阻塞至 Arrive 组完成，与 Arrive 构成屏障对。
- [Arrive（Cube核间管理）](arrive.md)（`same_topic`）：Arrive（Cube核间管理） 与《GroupBarrier》的实质衔接是：GroupBarrier Arrive 必须与构造、workspace、Wait 和 usage 配套，才能形成可闭合的组内 barrier。
- [GetWorkspaceLen](get_workspace_len.md)（`same_topic`）：GetWorkspaceLen 与《GroupBarrier》的实质衔接是：GetWorkspaceLen 是 GroupBarrier 使用流程的第一步；返回的 GM 长度供构造函数绑定，随后由 Arrive/Wait 完成分组屏障。
- [GroupBarrier使用说明](group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《GroupBarrier》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [GroupBarrier构造函数](group_barrier_constructor.md)（`same_topic`）：GroupBarrier构造函数 与《GroupBarrier》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
<!-- cannbot:related:end -->
