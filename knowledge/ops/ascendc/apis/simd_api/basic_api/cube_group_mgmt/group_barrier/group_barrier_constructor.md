---
type: API
title: GroupBarrier构造函数
description: 创建GroupBarrier对象，通过设置构造函数参数，确定Arrive组的Block个数和Wait组的Block个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/GroupBarrier/GroupBarrier_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# GroupBarrier构造函数

创建 GroupBarrier 对象，确定 Arrive 组和 Wait 组的 Block 个数，用于同一 CubeResGroupHandle 内 AIV 间的依赖同步。

原型：`__aicore__ inline GroupBarrier(GM_ADDR workspace, uint8_t arriveBlockDim, uint8_t waitBlockDim)`。参数：workspace（GM 工作空间地址）、arriveBlockDim（Arrive 组 Block 数量）、waitBlockDim（Wait 组 Block 数量）。Arrive 组所有 Block 调用 Arrive 后，Wait 组 Block 才能从 Wait 返回。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [Cube核间管理Wait](wait.md)（`related`）：GroupBarrier构造函数 与《Cube核间管理Wait》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GetResGroupBarrierWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_group_barrier_work_space_size.md)（`related`）：GroupBarrier构造函数 与《GetResGroupBarrierWorkSpaceSize》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GetWorkspaceLen](get_workspace_len.md)（`related`）：GroupBarrier构造函数 与《GetWorkspaceLen》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [Arrive（Cube核间管理）](arrive.md)（`same_topic`）：GroupBarrier构造函数 与《Arrive（Cube核间管理）》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GroupBarrier](group_barrier.md)（`same_topic`）：GroupBarrier构造函数 与《GroupBarrier》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GroupBarrier使用说明](group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《GroupBarrier构造函数》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
<!-- cannbot:related:end -->
