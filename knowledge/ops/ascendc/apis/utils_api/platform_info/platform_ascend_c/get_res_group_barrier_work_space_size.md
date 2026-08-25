---
type: API
title: GetResGroupBarrierWorkSpaceSize
description: 获取GroupBarrier所需要的workspace空间大小。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetResGroupBarrierWorkSpaceSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetResGroupBarrierWorkSpaceSize

## 功能说明
获取GroupBarrier所需要的workspace空间大小。
## 函数原型
## 参数说明
无
## 返回值说明
当前GroupBarrier所需要的workspace大小。
## 约束说明
无。

<!-- cannbot:related:start -->
## 相关

- [GroupBarrier使用说明](../../../simd_api/basic_api/cube_group_mgmt/group_barrier/group_barrier_usage.md)（`related`）：《GroupBarrier使用说明》明确“当同一个CubeResGroupHandle中的两个AIV任务之间存在依赖关系时，可以使用GroupBarrier控制同步。假设一组AIV A做完任务x以后，另外一组AIV B才可以开始后续业务，称AIV A组为Arrive组，AIV B组为Wait组。”；它与《GetResGroupBarrierWorkSpaceSize》的“获取GroupBarrier所需要的workspace空间大小。”在实际调用参数、数据流或结果校验上直接衔接。
- [GroupBarrier构造函数](../../../simd_api/basic_api/cube_group_mgmt/group_barrier/group_barrier_constructor.md)（`related`）：GroupBarrier构造函数 与《GetResGroupBarrierWorkSpaceSize》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [GetWorkspaceLen](../../../simd_api/basic_api/cube_group_mgmt/group_barrier/get_workspace_len.md)（`same_topic`）：《GetWorkspaceLen》明确“返回当前GroupBarrier所占用的Global Memory消息空间大小。”；它与《GetResGroupBarrierWorkSpaceSize》的“获取GroupBarrier所需要的workspace空间大小。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
