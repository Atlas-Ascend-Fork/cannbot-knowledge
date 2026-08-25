---
type: API
title: 同步控制
description: 同步控制接口集合，涵盖系统同步概述、核内同步、核间同步和任务间同步。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/sync_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 同步控制

AI Core 同步分三类：核内同步、核间同步和任务间同步。

核内同步包括 SetFlag/WaitFlag（多流水间同步）、PipeBarrier（单流水同步）、DataSyncBarrier（等待内存访问完成）、Lock/Unlock（异步流水锁机制）。核间同步包括 CrossCoreSetFlag/WaitFlag（多核硬件同步）、IBSet/IBWait（全局内存软件同步）、SyncAll（全核同步）、InitDetermineComputeWorkspace/NotifyNextBlock/WaitPreBlock（确定性计算升序执行）。任务间同步包括 SetNextTaskStart/WaitPreTaskEnd（SuperKernel 子 Kernel 间并行）。
