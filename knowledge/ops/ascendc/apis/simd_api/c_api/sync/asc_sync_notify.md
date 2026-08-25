---
type: API
title: AscSyncNotify
description: 与asc_sync_wait配对使用，实现AI Core内部不同流水之间的同步控制，当源流水前序指令完成后设置标志位。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_notify.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncNotify

如图1所示，与asc_sync_wait配对使用，用于实现AI Core内部不同流水之间的同步控制，asc_sync_notify和asc_sync_wait各自的功能如下： 图1  asc_sync_notify和asc_sync_wait接口功能示意图
约束：pipe与tpipe并非任意组合，两者组合的取值存在限制：针对不同产品，AIC与AIV中支持的组合不同，具体请参考核内同步分类中的表2和表3。；相同源流水、相同目标流水、相同id下，连续使用asc_sync_notify会引发未定义行为。；本接口需与asc_sync_wait配对使用，配对的两条调用其pipe、tpipe、id三个参数必须完全一致。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
