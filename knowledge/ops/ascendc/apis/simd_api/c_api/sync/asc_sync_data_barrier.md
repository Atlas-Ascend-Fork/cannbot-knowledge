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

- [DataCopyPad 后未先同步 Cast 导致低精度 NaN](../../../../runbooks/precision/mte2_barrier_must_precede_vector_cast.md)（`exemplifies`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《DataCopyPad 后未先同步 Cast 导致低精度 NaN》提供“MTE2 搬入后把 PipeBarrier 放在 Cast 之后过晚；应先同步，再由 Vector Cast 消费 LocalTensor。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线](../../../../runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)（`exemplifies`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线》提供“dav-3510 编译器不接受 PIPE_S 作为 PipeBarrier 模板参数；移除该屏障并保留 UB 写后与 DMA 写后的有效同步。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [asc_dci（缓存控制）](../cache_ctrl/asc_dci.md)（`related`）：asc_dci 前必须先执行 DataBarrier 等待所有内存访问结束，否则脏缓存行可能在未完成写回时被直接丢弃。
- [DataSyncBarrier](../../basic_api/sync_control/intra_core_sync/data_sync_barrier_isasi.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《DataSyncBarrier》提供“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，可通过模板参数控制需要等待的内存位置，用于解决Scalar的内存依赖。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [PipeBarrier](../../basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《PipeBarrier》提供“完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [asc_sync（同步）](asc_sync.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《asc_sync（同步）》提供“等待所有流水线操作完成。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
<!-- cannbot:related:end -->
