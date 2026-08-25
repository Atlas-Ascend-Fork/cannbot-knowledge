---
type: API
title: AscSyncWait
description: 等待特定的同步标志，阻塞当前流水线直到条件满足，与asc_sync_notify配对使用。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncWait

等待特定的同步标志，阻塞当前流水线直到条件满足。
函数原型：void asc_sync_wait(pipe_t pipe, pipe_t tpipe, event_t id)
约束：asc_sync_notify和asc_sync_wait必须成对使用。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [asc_sync（同步）](asc_sync.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncWait》明确提供“等待特定的同步标志，阻塞当前流水线直到条件满足，与asc_sync_notify配对使用。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscSyncNotify](asc_sync_notify.md)（`same_topic`）：AscSyncWait 与《AscSyncNotify》的实质衔接是：AscSyncWait 与 AscSyncNotify 是同一事件的等待/通知对，核内同步概述解释 event id 与流水依赖。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：AscSyncWait 与《核内同步能力概述》的实质衔接是：AscSyncWait 与 AscSyncNotify 是同一事件的等待/通知对，核内同步概述解释 event id 与流水依赖。
<!-- cannbot:related:end -->
