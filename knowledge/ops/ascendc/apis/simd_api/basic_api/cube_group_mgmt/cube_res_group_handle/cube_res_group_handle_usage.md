---
type: API
title: CubeResGroupHandle
description: 在分离模式下对AI Core计算资源分组，通过Client和Server架构实现AIV与AIC间的消息通信和任务分发。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/CubeResGroupHandle_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2]
---

# CubeResGroupHandle

在分离模式下对 AI Core 计算资源分组，通过 Client-Server 架构实现 AIV（Vector Core）与 AIC（Cube Core）间的消息通信和任务分发。

使用流程：CreateCubeResGroup 创建资源组 → AIV 调用 AllocMessage 申请消息空间 → 构造 CubeMsgType 消息并 PostMessage 发送 → AIC 通过回调函数处理消息 → FreeMessage 释放 → AIV 调用 Wait 等待处理完成。消息队列深度固定为 4，消息状态含 FREE、IDLE、PROCESSING、DONE 等。支持 PostFakeMsg/SetSkipMsg 实现消息合并，SetQuit 发送退出消息。CubeMsgType 由用户定义，包含 tilingData、msgState、msgOffset 等字段。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《CubeResGroupHandle》明确“在分离模式下对AI Core计算资源分组，通过Client和Server架构实现AIV与AIC间的消息通信和任务分发。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [Cube核间管理Wait](wait.md)（`related`）：PostMessage 后 AIV 必须用 Wait 等待 AIC 把消息状态推进到 DONE，才能安全回收或继续。
- [PostMessage](post_message.md)（`related`）：AIV 在 AllocMessage 填好 CubeMsgType 后通过 PostMessage 提交给 AIC 回调，是 usage 中任务分发的核心交接点。
- [CreateCubeResGroup](create_cube_res_group.md)（`same_topic`）：CreateCubeResGroup 只完成句柄和队列/事件资源创建，usage 给出创建后的消息分配、发送、等待和退出完整生命周期。
- [CubeResGroupHandle](cube_res_group_handle.md)（`same_topic`）：CubeResGroupHandle 与《CubeResGroupHandle》的实质衔接是：CubeResGroupHandle 管理消息、队列、barrier 与 KFC workspace 生命周期，并约束 Cube 核执行。
- [GroupBarrier使用说明](../group_barrier/group_barrier_usage.md)（`same_topic`）：GroupBarrier使用说明 与《CubeResGroupHandle》的实质衔接是：GroupBarrier 用法明确要求 workspace 查询、对象构造、Arrive 与 Wait；CubeResGroupHandle 是这些分组任务所属的资源组。
- [UpdateKfcWorkspace](../kfc_workspace/update_kfc_workspace.md)（`same_topic`）：UpdateKfcWorkspace 与《CubeResGroupHandle》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
<!-- cannbot:related:end -->
