---
type: API
title: AscSyncDataBarrier
description: 阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_data_barrier.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncDataBarrier

阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束，用于解决Scalar的内存依赖。
函数原型：void asc_sync_data_barrier(mem_dsb_t arg)
约束：mem_dsb_t类型的入参必须直接传递枚举值字面量。；等待的内存位置取值为DSB_ALL时，只能等待GM和UB的访问指令，不包括其他内存位置，例如L0C Buffer、L1 Buffer。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [asc_dci（缓存控制）](../cache_ctrl/asc_dci.md)（`related`）：asc_dci 的硬约束是“在调用asc_dci之前，需调用asc_sync_data_barrier插入DSB_ALL指令”；barrier API执行“阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束”。该屏障必须先完成，才能安全执行数据缓存失效。
<!-- cannbot:related:end -->
