---
type: API
title: AscSyncVec
description: 针对PIPE_V流水线执行同步操作。无入参函数原型已废弃，请使用asc_sync执行所有流水线的同步。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_vec.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncVec

无入参函数原型asc_sync_vec()接口已废弃，请使用asc_sync执行针对所有流水线的同步操作。 针对PIPE_V流水线执行同步操作。
函数原型：void asc_sync_vec(int id)
约束：同步ID的取值范围为：0-7。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [arch35 Select 异步SIMT同步失效致分支错选](../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《AscSyncVec》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [asc_sync（同步）](asc_sync.md)（`same_topic`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncVec》明确提供“针对PIPE_V流水线执行同步操作。无入参函数原型已废弃，请使用asc_sync执行所有流水线的同步。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
<!-- cannbot:related:end -->
