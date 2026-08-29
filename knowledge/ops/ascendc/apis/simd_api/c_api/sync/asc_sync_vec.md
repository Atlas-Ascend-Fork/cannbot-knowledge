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
