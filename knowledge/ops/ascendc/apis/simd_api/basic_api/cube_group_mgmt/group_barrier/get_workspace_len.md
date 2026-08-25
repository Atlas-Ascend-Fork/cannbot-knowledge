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

<!-- cannbot:related:start -->
## 相关

- [Arrive（Cube核间管理）](arrive.md)（`related`）：Arrive（Cube核间管理） 与《GetWorkspaceLen》的实质衔接是：GroupBarrier Arrive 必须与构造、workspace、Wait 和 usage 配套，才能形成可闭合的组内 barrier。
- [GroupBarrier构造函数](group_barrier_constructor.md)（`related`）：GroupBarrier构造函数 与《GetWorkspaceLen》的实质衔接是：GroupBarrier 构造依赖 workspace 并产生可用于 Arrive/Wait 的组对象；用法页和空间查询闭合初始化、到达、等待流程。
- [Cube核间管理Wait](wait.md)（`same_topic`）：GetWorkspaceLen 与《Cube核间管理Wait》的实质衔接是：GetWorkspaceLen 是 GroupBarrier 使用流程的第一步；返回的 GM 长度供构造函数绑定，随后由 Arrive/Wait 完成分组屏障。
- [GetResGroupBarrierWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_res_group_barrier_work_space_size.md)（`same_topic`）：《GetWorkspaceLen》明确“返回当前GroupBarrier所占用的Global Memory消息空间大小。”；它与《GetResGroupBarrierWorkSpaceSize》的“获取GroupBarrier所需要的workspace空间大小。”在实际调用参数、数据流或结果校验上直接衔接。
- [GroupBarrier](group_barrier.md)（`same_topic`）：GetWorkspaceLen 与《GroupBarrier》的实质衔接是：GetWorkspaceLen 是 GroupBarrier 使用流程的第一步；返回的 GM 长度供构造函数绑定，随后由 Arrive/Wait 完成分组屏障。
- [GroupBarrier使用说明](group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《GetWorkspaceLen》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
<!-- cannbot:related:end -->
