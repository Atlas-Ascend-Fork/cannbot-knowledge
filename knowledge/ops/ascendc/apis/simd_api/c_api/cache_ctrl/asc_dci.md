---
type: API
title: asc_dci（缓存控制）
description: 数据缓存失效，该指令用于使整个数据缓存无效化，且不会对处于“脏”状态的缓存行执行写回操作。换言之，所有缓存行将被直接标记为无效，其修改过但尚未同步至主存的数据将被丢弃。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_dci.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_dci（缓存控制）

数据缓存失效，该指令用于使整个数据缓存无效化，且不会对处于“脏”状态的缓存行执行写回操作。换言之，所有缓存行将被直接标记为无效，其修改过但尚未同步至主存的数据将被丢弃。

约束：在调用asc_dci之前，需调用asc_sync_data_barrier插入DSB_ALL指令，等待所有内存访问指令执行结束。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSyncDataBarrier](../sync/asc_sync_data_barrier.md)（`related`）：asc_dci 的硬约束是“在调用asc_dci之前，需调用asc_sync_data_barrier插入DSB_ALL指令”；barrier API执行“阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束”。该屏障必须先完成，才能安全执行数据缓存失效。
<!-- cannbot:related:end -->
