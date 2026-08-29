---
type: API
title: AscSyncMte2
description: 针对PIPE_MTE2流水线执行同步操作，保证其前序指令全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能执行。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_mte2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncMte2

针对PIPE_MTE2流水线执行同步操作。其作用是保证PIPE_MTE2流水线中前序指令（如GM到UB的数据搬运）全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能开始执行。
函数原型：void asc_sync_mte2(int id)
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
