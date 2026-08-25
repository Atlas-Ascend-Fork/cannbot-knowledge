---
type: API
title: 核内同步
description: 核内同步接口索引页，汇总TQueSync模板参数、SetFlag/WaitFlag、PipeBarrier、DataSyncBarrier、Mutex及Lock/Unlock等。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核内同步

核内同步接口协调同一核内不同流水线之间的执行顺序。SetFlag/WaitFlag及ISASI变体实现多流水线同步，SetFlag发送通知，WaitFlag阻塞等待。
PipeBarrier(ISASI)实现单流水线内指令同步（不支持PIPE_S）；DataSyncBarrier(ISASI)阻塞后续指令直到此前内存访问完成。Lock/Unlock提供流水线锁机制，Mutex(ISASI)封装互斥操作。AllocMutexID/ReleaseMutexID(ISASI)用于分配和释放互斥ID。TQueSync模板参数用于配置队列同步属性。
