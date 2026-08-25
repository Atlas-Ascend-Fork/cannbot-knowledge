---
type: API
title: ReleaseMutexID
description: 从框架释放一个MutexID，与AllocMutexID配合使用，防止MutexID耗尽。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/ReleaseMutexID_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ReleaseMutexID

头文件路径为："basic_api/kernel_common.h"。

从框架释放一个MutexID，与AllocMutexID配合使用。

参数：id(输入): MutexID类型，应传入调用AllocMutexID获得的MutexID。

约束：MutexID有数量限制，使用结束后应立即调用ReleaseMutexID释放，防止MutexID耗尽。

仅 Ascend 950PR/Ascend 950DT 支持。
