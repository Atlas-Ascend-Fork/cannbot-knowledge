---
type: API
title: 系统同步能力概述（同步控制）
description: 在编程中，同步是指协调多个执行单元（如线程、进程等）对共享资源的访问顺序和时机来确保程序的正确性。如果没有同步来严格控制执行顺序，则会出现结果不一致、行为不可预测等多种问题。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/system_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 系统同步能力概述（同步控制）

同步是指协调多个执行单元对共享资源的访问顺序和时机来确保程序正确性。AI Core 的同步分为三类：核内同步、核间同步与任务间同步。
核内同步包括 SetFlag/WaitFlag（多流水同步）、PipeBarrier（单流水同步）、DataSyncBarrier（内存访问屏障）、Lock/Unlock（锁机制同步）。
核间同步包括 CrossCoreSetFlag/CrossCoreWaitFlag（多核硬件同步）、IBSet/IBWait（软件同步）、SyncAll（全核同步）、InitDetermineComputeWorkspace/NotifyNextBlock/WaitPreBlock（确定性计算同步）。
任务间同步包括 SetNextTaskStart 与 WaitPreTaskEnd，用于 SuperKernel 子 Kernel 间的并行优化。
各类同步接口分为硬件同步与软件同步两类，硬件同步通过片上信号量实现，软件同步通过全局内存读写实现。
