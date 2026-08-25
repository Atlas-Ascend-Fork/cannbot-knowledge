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

<!-- cannbot:related:start -->
## 相关

- [Lock](lock.md)（`related`）：Lock 在 TPipe-TQue 范式中明确消费 AllocMutexID 返回的 ID，并以 pipe+ID 阻塞目标流水；这是分配结果的直接使用点。
- [Unlock](unlock.md)（`related`）：Unlock 必须与先前 Lock 使用相同 pipe 和 MutexID，而该 ID 在 TPipe-TQue 范式来自 AllocMutexID；它补齐分配后锁的释放动作。
- [AscLock](../../../c_api/sync/asc_lock.md)（`same_topic`）：《AllocMutexID》给出“从框架获取并占用一个MutexID，与ReleaseMutexID配合使用，获取的MutexID可传入Mutex::Lock/Unlock接口用于流水同步。”；该约束/探针可直接复现、解释或前置验证《AscLock》中的“用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。”。
- [ReleaseMutexID](release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《AllocMutexID》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
<!-- cannbot:related:end -->
