---
type: API
title: AscUnlock
description: 用于同步AI Core内部异步流水的指令，在当前流水的前序指令执行完成后根据mutex_id释放对应Mutex。须与asc_lock成对使用。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_unlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscUnlock

用于同步AI Core内部异步流水的指令，直到当前流水的前序指令执行完成后，根据mutex_id释放对应Mutex。

相对于asc_sync_notify/asc_sync_wait同步机制，使用asc_lock/asc_unlock接口有以下优势：

- 内聚性更强，使用时与其它流水线解耦，可以简化反向同步。以PIPE_MTE2与PIPE_V之间同步为例，对比如下：

    其中EVENT_ID0为同步ID，取值范围为[0, 7]；mutex_id取值范围为[0, 31]。
- 可以使用更多的同步信号量。

字段：pipe：该指令的执行流水线。；mutex_id：mutex标号。取值范围[0, 31]。；mode：可选参数，用于指定是否阻塞流水线，默认值为ASC_LOCK_BLOCK。 &bull; ASC_LOCK_BLOCK：该指令等待pipe所对应的流水线中所有前置指令完成后执行。 &bull; ASC_LOCK_NON_BLOCK：该指令等待pipe所对应的流水线中所有前置指令完成且相同mutex_id的所有asc_unlock指令执行完成后执行。

约束：必须与asc_lock搭配使用，且需要使用相同的mutex_id与mode。此外，asc_unlock必须始终插在对应的asc_lock指令之后，否则会出现未定义的硬件行为。；具有相同mutex_id的asc_lock与asc_unlock组合，无论pipe与mode是否相同，均不得在编程顺序中嵌套，否则硬件行为将不可预测。；对于程序顺序中连续出现的，具有相同pipe与mutex_id的指令对，后一个asc_lock将不再阻塞流水线运行，若需实现同一流水线的依赖关系，则必须使用指令asc_sync_pipe。

支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLock](asc_lock.md)（`related`）：AscUnlock 必须在相同 mutex_id/mode 的 AscLock 之后，二者共同形成互斥同步区间。
- [Lock](../../basic_api/sync_control/intra_core_sync/lock.md)（`same_topic`）：Lock 与《AscUnlock》的实质衔接是：Lock 必须用 AllocMutexID 得到 mutex，并与 Unlock、ReleaseMutexID 成对；C Lock/Unlock 和核内同步概述共享同一阻塞流水契约。
- [ReleaseMutexID](../../basic_api/sync_control/intra_core_sync/release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《AscUnlock》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
<!-- cannbot:related:end -->
