---
type: API
title: Cube分组管理（ISASI）
description: Cube 分组管理（ISASI）接口总览，涵盖 CubeResGroupHandle、GroupBarrier、KfcWorkspace 等组件。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/cube_group_mgmt_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cube分组管理（ISASI）

Cube 分组管理（ISASI）接口总览，涵盖 CubeResGroupHandle、GroupBarrier、KfcWorkspace 等组件。

本接口组包含 CubeResGroupHandle, GroupBarrier, KfcWorkspace。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [CreateCubeResGroup](cube_res_group_handle/create_cube_res_group.md)（`related`）：CreateCubeResGroup 自动完成消息队列空间和同步事件分配，并明确优先于手工构造，可避免队列空间冲突；这是落地资源分组的关键选择约束。
- [GroupBarrier使用说明](group_barrier/group_barrier_usage.md)（`related`）：分组管理总览只定位组件，GroupBarrierUsage 给出 Arrive 组/Wait 组依赖模型和同步时机，能直接指导跨 AIV 分组任务依赖的实现。
<!-- cannbot:related:end -->
