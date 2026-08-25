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

<!-- cannbot:related:start -->
## 相关

- [任务间同步](inter_task_sync/inter_task_sync.md)（`related`）：系统同步能力概述（同步控制） 与《任务间同步》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
- [同步控制](../../c_api/sync/sync_control.md)（`related`）：同步控制 与《系统同步能力概述（同步控制）》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [核内同步能力概述](intra_core_sync/intra_core_sync_overview.md)（`related`）：系统同步能力概述（同步控制） 与《核内同步能力概述》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
- [核间同步能力概述](inter_core_sync/inter_core_sync_overview.md)（`related`）：系统同步能力概述（同步控制） 与《核间同步能力概述》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
<!-- cannbot:related:end -->
