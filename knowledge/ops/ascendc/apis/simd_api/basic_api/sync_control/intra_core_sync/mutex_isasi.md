---
type: API
title: Mutex(ISASI)
description: Mutex用于核内异步流水指令之间的同步控制，其功能类似于传统CPU中的锁机制。通过先锁定再释放指定流水来完成流水间的同步依赖，锁定/解锁指定流水对应Lock/Unlock接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/Mutex_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Mutex(ISASI)

Mutex 用于核内异步流水指令之间的同步控制，功能类似传统 CPU 中的锁机制。通过先锁定再释放指定流水完成流水间的同步依赖。
Lock 接口根据 MutexID 获取 Mutex，若已被锁定则阻塞后续指定流水指令队列；Unlock 接口在当前流水前序指令执行完成后根据 MutexID 释放对应 Mutex。
TPipe-TQue 框架编程范式下 MutexID 通过 AllocMutexID/ReleaseMutexID 申请释放；静态 Tensor 编程范式下由开发者自行管理，建议使用 0-27，28-31 为系统预留。
相比 SetFlag/WaitFlag 同步机制，Lock/Unlock 接口内聚性更强、与其他流水线解耦、可简化反向同步，且支持更多同步信号量。
仅 Ascend 950PR/950DT 支持，接口标注为 ISASI 类别，不保证跨硬件版本兼容。

<!-- cannbot:related:start -->
## 相关

- [Lock](lock.md)（`same_topic`）：Lock 与《Mutex(ISASI)》的实质衔接是：Lock 必须用 AllocMutexID 得到 mutex，并与 Unlock、ReleaseMutexID 成对；C Lock/Unlock 和核内同步概述共享同一阻塞流水契约。
- [ReleaseMutexID](release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《Mutex(ISASI)》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
<!-- cannbot:related:end -->
