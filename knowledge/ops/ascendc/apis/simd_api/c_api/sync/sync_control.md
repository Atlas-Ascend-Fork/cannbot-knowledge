---
type: API
title: 同步控制
description: SIMD C API同步控制类接口汇总，提供lock、sync、barrier、notify等多级同步与锁机制。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/sync_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 同步控制

C API同步控制接口提供多级同步与锁机制。全核同步含asc_sync及asc_sync_block_arrive/wait、asc_sync_inter_arrive/wait、asc_sync_subblock_arrive/wait、asc_sync_intra_arrive/wait，支持block/subblock/inter/intra多级粒度。
流水线同步含asc_sync_pipe/mte2/mte3/vec，协调不同流水线执行顺序。asc_sync_data_barrier提供数据屏障，asc_sync_notify/asc_sync_wait实现通知等待模式。asc_lock/asc_unlock提供互斥锁机制。

<!-- cannbot:related:start -->
## 相关

- [arch35 Select 异步SIMT同步失效致分支错选](../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《同步控制》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [AscSyncIntraArrive](asc_sync_intra_arrive.md)（`related`）：《AscSyncIntraArrive》处理“与asc_sync_intra_wait配合使用，用于block内不同Core的流水线同步，向同步寄存器发送同步信号。”。《同步控制》明确“SIMD C API同步控制类接口汇总，提供lock、sync、barrier、notify等多级同步与锁机制。”，可直接用于核对核内 arrive/wait 配对、可见性范围及双 AIV flag 路由缺陷。
- [asc_sync（同步）](asc_sync.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《同步控制》明确提供“SIMD C API同步控制类接口汇总，提供lock、sync、barrier、notify等多级同步与锁机制。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [任务间同步](../../basic_api/sync_control/inter_task_sync/inter_task_sync.md)（`related`）：同步控制 与《任务间同步》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [同步与内存栅栏](../../../simt_api/sync_and_memory_fence/sync_and_memory_fence.md)（`related`）：同步控制 与《同步与内存栅栏》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [同步控制](../../basic_api/sync_control/sync_control.md)（`related`）：同步控制 与《同步控制》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [核间同步能力概述](../../basic_api/sync_control/inter_core_sync/inter_core_sync_overview.md)（`related`）：同步控制 与《核间同步能力概述》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [系统同步能力概述（同步控制）](../../basic_api/sync_control/system_sync_overview.md)（`related`）：同步控制 与《系统同步能力概述（同步控制）》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
<!-- cannbot:related:end -->
