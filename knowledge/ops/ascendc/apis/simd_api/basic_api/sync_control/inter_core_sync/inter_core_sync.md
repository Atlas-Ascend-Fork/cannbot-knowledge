---
type: API
title: 核间同步
description: 核间同步接口索引页，汇总IBSet、IBWait、SyncAll、CrossCoreSetFlag/WaitFlag(ISASI)及NotifyNextBlock/WaitPreBlock。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/inter_core_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 核间同步

核间同步接口协调多个AIC/AIV核之间的执行顺序。硬件同步类接口包括CrossCoreSetFlag/CrossCoreWaitFlag(ISASI)和SyncAll，前者负责通知与阻塞等待，后者支持纯Vector全核同步和融合算子三阶段同步。
软件同步类接口包括IBSet/IBWait（全局内存信号量轮询）和SyncAll的软件模式。InitDetermineComputeWorkspace/NotifyNextBlock/WaitPreBlock三者组合使用，确保多AIV核按blockIdx升序执行，适用于确定性计算场景。
