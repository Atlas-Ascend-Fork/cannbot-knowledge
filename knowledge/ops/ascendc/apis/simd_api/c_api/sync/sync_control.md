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
