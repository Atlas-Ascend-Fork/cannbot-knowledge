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

- [AscUnlock](asc_unlock.md)（`related`）：asc_lock与asc_unlock必须严格成对使用，并使用相同的mutex_id与mode。；必须与asc_lock搭配使用，且需要使用相同的mutex_id与mode。。两端相互声明同一 mutex_id/mode 的成对协议：asc_lock 获取并阻塞流水，asc_unlock 在前序指令完成后释放；联合阅读才能确定合法同步序列。
<!-- cannbot:related:end -->
