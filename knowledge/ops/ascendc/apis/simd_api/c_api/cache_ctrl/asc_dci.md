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

- [设置DCI编译选项来减少算子尾开销](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md)（`explains`）：指南把 DCI 缓存失效用于减少算子尾部维护开销，并说明编译选项和适用条件。
- [AscSyncDataBarrier](../sync/asc_sync_data_barrier.md)（`related`）：asc_dci 前必须先执行 DataBarrier 等待所有内存访问结束，否则脏缓存行可能在未完成写回时被直接丢弃。
- [asc_dcci_entire](../../../simt_api/memory_access_functions/asc_dcci_entire.md)（`same_topic`）：asc_dcci_entire 与《asc_dci（缓存控制）》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
<!-- cannbot:related:end -->
