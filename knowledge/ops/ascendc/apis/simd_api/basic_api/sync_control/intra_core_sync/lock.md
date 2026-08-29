---
type: API
title: Lock
description: 根据MutexID获取Mutex锁，若Mutex已被锁定则阻塞后续指定流水指令队列，直到对应MutexID的Mutex被Unlock，需与Unlock严格成对使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/Lock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Lock

头文件路径为："basic_api/kernel_common.h"。

根据MutexID获取Mutex，若Mutex已被锁定，将阻塞后续指定流水指令队列，直到当前流水的前序指令中对应MutexID的Mutex被Unlock。

参数：pipe: 模板参数，表示流水类别。支持PIPE_S、PIPE_M、PIPE_V、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX，各流水类型的含义请参考硬件流水类型。；id(输入): 进行流水同步管理的MutexID。在不同编程范式中，该ID的获取以及释放方式不同，详细情况参考约束说明。

约束：- 每个锁有固定的一个MutexID，在不同编程范式中，该ID的获取以及释放方式不同
    - 采用TPipe-TQue框架编程范式时，MutexID需要通过AllocMutexID/ReleaseMutexID进行申请释放。
    - 采用静态Tensor编程范式时，MutexID由开发者自行管理，建议使用0-27，28-31为系统内部规划预留，不建议使用。
- 对于同一个MutexID，必须先执行Lock，然后才能执行Unlock，且指定的pipe需要相同。如果Lock和Unlock没有按照这种"成对出现"的顺序排列，硬件行为将不可预测。以下是常见的错误用法与正确用法示例
- 使用相同MutexID、相同流水的两组Lock/UnLock指令时，第二次Lock不会再阻塞流水，这种情况建议使用PipeBarrier接口。以下是错误用法与正确用法的示例

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Unlock](unlock.md)（`related`）：根据MutexID获取Mutex，若Mutex已被锁定，将阻塞后续指定流水指令队列，直到当前流水的前序指令中对应MutexID的Mutex被Unlock。；直到当前流水的前序指令执行完成后，根据MutexID释放对应Mutex。。Lock 的阻塞条件以同 MutexID 的 Unlock 为解除点，Unlock 又要求前序流水完成后释放，二者共同定义成对互斥协议。
<!-- cannbot:related:end -->
