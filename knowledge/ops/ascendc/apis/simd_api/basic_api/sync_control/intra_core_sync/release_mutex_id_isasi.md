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

<!-- cannbot:related:start -->
## 相关

- [AscLock](../../../c_api/sync/asc_lock.md)（`related`）：《ReleaseMutexID》明确“从框架释放一个MutexID，与AllocMutexID配合使用，防止MutexID耗尽。”；它与《AscLock》的“用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。”在实际调用参数、数据流或结果校验上直接衔接。
- [AllocMutexID](alloc_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《AllocMutexID》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [AscUnlock](../../../c_api/sync/asc_unlock.md)（`same_topic`）：ReleaseMutexID 与《AscUnlock》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [Lock](lock.md)（`same_topic`）：ReleaseMutexID 与《Lock》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [Mutex(ISASI)](mutex_isasi.md)（`same_topic`）：ReleaseMutexID 与《Mutex(ISASI)》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [Unlock](unlock.md)（`same_topic`）：ReleaseMutexID 与《Unlock》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [核内同步](intra_core_sync.md)（`same_topic`）：ReleaseMutexID 与《核内同步》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：ReleaseMutexID 与《核内同步能力概述》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
<!-- cannbot:related:end -->
