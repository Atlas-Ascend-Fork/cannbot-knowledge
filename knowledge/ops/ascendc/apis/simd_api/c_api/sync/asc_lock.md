---
type: API
title: AscLock
description: 用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_lock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscLock

该接口用于AI Core内部异步流水线之间的同步，可按需阻塞指定流水线的执行。 根据mutex_id获取Mutex，若Mutex已被锁定，将阻塞后续指定流水指令队列，直到当前流水的前序指令中对应mutex_id的Mutex被asc_unlock释放。 相对于asc_sync_notify/asc_sync_wait同步机制，使用asc_lock/asc_unlock接口有以下优势：
函数原型：void asc_lock(pipe_t pipe, uint8_t mutex_id)
约束：asc_lock与asc_unlock必须严格成对使用，并使用相同的mutex_id与mode。此外，对应的asc_unlock必须始终写在asc_lock之后，否则硬件行为无定义。；对于mutex_id相同的asc_lock与asc_unlock组合，无论pipe和mode是否相同，都不得在代码中嵌套使用，否则硬件行为将不可预测。；成对使用的asc_lock和asc_unlock必须配置相同的mode，否则硬件行为将不可预测。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscUnlock](asc_unlock.md)（`related`）：AscUnlock 必须在相同 mutex_id/mode 的 AscLock 之后，二者共同形成互斥同步区间。
- [ReleaseMutexID](../../basic_api/sync_control/intra_core_sync/release_mutex_id_isasi.md)（`related`）：《ReleaseMutexID》明确“从框架释放一个MutexID，与AllocMutexID配合使用，防止MutexID耗尽。”；它与《AscLock》的“用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。”在实际调用参数、数据流或结果校验上直接衔接。
- [AllocMutexID](../../basic_api/sync_control/intra_core_sync/alloc_mutex_id_isasi.md)（`same_topic`）：《AllocMutexID》给出“从框架获取并占用一个MutexID，与ReleaseMutexID配合使用，获取的MutexID可传入Mutex::Lock/Unlock接口用于流水同步。”；该约束/探针可直接复现、解释或前置验证《AscLock》中的“用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。”。
- [Lock](../../basic_api/sync_control/intra_core_sync/lock.md)（`same_topic`）：《Lock》明确“根据MutexID获取Mutex锁，若Mutex已被锁定则阻塞后续指定流水指令队列，直到对应MutexID的Mutex被Unlock，需与Unlock严格成对使用。”；它与《AscLock》的“用于AI Core内部异步流水线之间的同步，根据mutex_id获取Mutex，可按需阻塞指定流水线的执行。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
