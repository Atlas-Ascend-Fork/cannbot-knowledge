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
