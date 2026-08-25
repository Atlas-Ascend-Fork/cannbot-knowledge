---
type: API
title: DataSyncBarrier
description: 阻塞后续指令执行，直到所有之前的内存访问指令执行结束，可通过模板参数控制需要等待的内存位置，用于解决Scalar的内存依赖。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/DataSyncBarrier_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# DataSyncBarrier

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束，用于解决Scalar的内存依赖。

参数：arg0: 模板参数，表示需要等待的内存位置，类型为MemDsbT，可取值为： &bull; ALL，等待GM和UB的访问指令（不包括其他内存位置，例如L0C Buf。

约束：等待的内存位置取值为ALL时，只能等待GM和UB的访问指令，不包括其他内存位置，例如L0C Buffer、L1 Buffer。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品 支持。

<!-- cannbot:related:start -->
## 相关

- [CrossCoreSetFlag](../inter_core_sync/cross_core_set_flag_isasi.md)（`related`）：CrossCore flag 作用于不同核，不是 DataSyncBarrier 的核内替代；同步域需严格区分。
- [PipeBarrier](pipe_barrier_isasi.md)（`related`）：PipeBarrier 只同步指定流水，而 DataSyncBarrier 建立更广的数据可见性；依赖范围决定选型。
- [SetFlag/WaitFlag](set_flag_wait_flag_isasi.md)（`related`）：明确 producer/consumer pipeline 时 flag/wait 可替代全局数据屏障，减少无关流水等待。
- [关键特性说明](key_features.md)（`related`）：需要更广数据可见性时使用 DataSyncBarrier，代价和范围均更大。
- [AscSyncDataBarrier](../../../c_api/sync/asc_sync_data_barrier.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《DataSyncBarrier》提供“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，可通过模板参数控制需要等待的内存位置，用于解决Scalar的内存依赖。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：概览解释 DataSyncBarrier、PipeBarrier 和 event 的同步范围，防止用过强/过弱屏障。
<!-- cannbot:related:end -->
