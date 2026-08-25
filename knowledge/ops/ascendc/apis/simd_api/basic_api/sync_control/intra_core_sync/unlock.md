---
type: API
title: Unlock
description: 当前流水的前序指令执行完成后，根据MutexID释放对应Mutex，需与Lock接口严格成对使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/Unlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Unlock

头文件路径为："basic_api/kernel_common.h"。

直到当前流水的前序指令执行完成后，根据MutexID释放对应Mutex。

参数：pipe: 模板参数，表示流水类别。支持PIPE_S、PIPE_M、PIPE_V、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX，各流水类型的含义请参考硬件流水类型。；id(输入): 进行流水同步管理的MutexID。在不同编程范式中，该ID的获取以及释放方式不同，详细情况参考Lock约束说明。

约束：参考Lock约束说明。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocMutexID](alloc_mutex_id_isasi.md)（`related`）：Unlock 必须与先前 Lock 使用相同 pipe 和 MutexID，而该 ID 在 TPipe-TQue 范式来自 AllocMutexID；它补齐分配后锁的释放动作。
- [Lock](lock.md)（`same_topic`）：Lock 与《Unlock》的实质衔接是：Lock 必须用 AllocMutexID 得到 mutex，并与 Unlock、ReleaseMutexID 成对；C Lock/Unlock 和核内同步概述共享同一阻塞流水契约。
- [ReleaseMutexID](release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《Unlock》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
<!-- cannbot:related:end -->
