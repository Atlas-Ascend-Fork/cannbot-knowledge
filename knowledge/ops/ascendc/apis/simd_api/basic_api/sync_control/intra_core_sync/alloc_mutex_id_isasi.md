---
type: API
title: AllocMutexID
description: 从框架获取并占用一个MutexID，与ReleaseMutexID配合使用，获取的MutexID可传入Mutex::Lock/Unlock接口用于流水同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/AllocMutexID_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AllocMutexID

头文件路径为："basic_api/kernel_common.h"。

从框架获取并占用一个MutexID，与ReleaseMutexID配合使用，管理MutexID的获取和释放。获取的MutexID可以传入Mutex::Lock/Mutex::Unlock接口使用，此时Mutex::Lock/Unlock可以与TQue等其他接口配合使用。

约束：MutexID有数量限制，使用结束后应立即调用ReleaseMutexID释放，防止MutexID耗尽。

仅 Ascend 950PR/Ascend 950DT 支持。
