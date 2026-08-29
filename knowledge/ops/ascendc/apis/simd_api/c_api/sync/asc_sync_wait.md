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

- [AscSyncNotify](asc_sync_notify.md)（`same_topic`）：约束：asc_sync_notify和asc_sync_wait必须成对使用。；本接口需与asc_sync_wait配对使用，配对的两条调用其pipe、tpipe、id三个参数必须完全一致。；wait 明确要求与 notify 成对，notify 进一步规定两端 pipe、tpipe 和 id 完全一致；两卡共同定义 AI Core 内流水同步握手。
<!-- cannbot:related:end -->
