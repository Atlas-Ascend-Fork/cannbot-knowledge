---
type: API
title: GroupBarrier使用说明
description: 当同一个CubeResGroupHandle中的两个AIV任务之间存在依赖关系时，可以使用GroupBarrier控制同步。假设一组AIV
  A做完任务x以后，另外一组AIV B才可以开始后续业务，称AIV A组为Arrive组，AIV B组为Wait组。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GroupBarrier_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# GroupBarrier使用说明

当同一 CubeResGroupHandle 中的两组 AIV 任务存在依赖关系时，使用 GroupBarrier 控制同步。Arrive 组完成任务后调用 Arrive()，Wait 组调用 Wait() 阻塞等待，直到 Arrive 组全部完成。

使用流程：GetWorkspaceLen 获取所需 GM 空间 → 分配 workspace → 构造 GroupBarrier(workspace, arriveBlockDim, waitBlockDim) → Arrive 组 AIV 调用 Arrive() → Wait 组 AIV 调用 Wait()。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [Cube分组管理（ISASI）](../cube_group_mgmt_isasi.md)（`related`）：分组管理总览只定位组件，GroupBarrierUsage 给出 Arrive 组/Wait 组依赖模型和同步时机，能直接指导跨 AIV 分组任务依赖的实现。
- [GetResGroupBarrierWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_group_barrier_work_space_size.md)（`related`）：《GroupBarrier使用说明》明确“当同一个CubeResGroupHandle中的两个AIV任务之间存在依赖关系时，可以使用GroupBarrier控制同步。假设一组AIV A做完任务x以后，另外一组AIV B才可以开始后续业务，称AIV A组为Arrive组，AIV B组为Wait组。”；它与《GetResGroupBarrierWorkSpaceSize》的“获取GroupBarrier所需要的workspace空间大小。”在实际调用参数、数据流或结果校验上直接衔接。
- [Arrive（Cube核间管理）](arrive.md)（`same_topic`）：GroupBarrier使用说明 与《Arrive（Cube核间管理）》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [CubeResGroupHandle](../cube_res_group_handle/cube_res_group_handle_usage.md)（`same_topic`）：GroupBarrier使用说明 与《CubeResGroupHandle》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [Cube核间管理Wait](wait.md)（`same_topic`）：GroupBarrier使用说明 与《Cube核间管理Wait》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [GetWorkspaceLen](get_workspace_len.md)（`same_topic`）：GroupBarrier使用说明 与《GetWorkspaceLen》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [GroupBarrier](group_barrier.md)（`same_topic`）：GroupBarrier使用说明 与《GroupBarrier》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [GroupBarrier构造函数](group_barrier_constructor.md)（`same_topic`）：GroupBarrier使用说明 与《GroupBarrier构造函数》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
<!-- cannbot:related:end -->
