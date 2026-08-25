---
type: API
title: asc_sync（同步）
description: 等待所有流水线操作完成。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_sync（同步）

等待所有流水线操作完成。
函数原型：void asc_sync()
约束：asc_sync会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅需阻塞单条流水线，应避免随意调用asc_sync，可选用asc_sync_pipe、asc_sync_mte2、asc_sync_mte3等接口精准控制，以提升性能。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [MTE2跨流水未建依赖导致UB读到上次调用残值](../../../../runbooks/precision/direct_mte_slot_reuse_needs_bidirectional_hard_events.md)（`exemplifies`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《MTE2跨流水未建依赖导致UB读到上次调用残值》明确提供“仅在必须采用逐元素 DMA 槽的安全回退中，用 TQue 与双向 HardEvent 防陈旧 UB；纯随机独立读取应先探测 SIMT 直访 GM 快路。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [TBuf 跨 MTE2 与 Vector 须队列交接](../../../../runbooks/precision/tbuf_mte2_to_vector_requires_queue_handoff.md)（`exemplifies`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《TBuf 跨 MTE2 与 Vector 须队列交接》明确提供“GM 数据写入裸 TBuf 后立刻由 V pipe 消费时，A3 与 Ascend950 的独立轨迹均出现数值错误、NaN 或非有限值位置不一致；改为 VECIN TQue 交接后定向及完整测试通过。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《asc_sync（同步）》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 __aicore__ 调 LocalMemBar 报 507035](../../../../runbooks/compilation/arch35_aicore_localmembar_507035.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《asc_sync（同步）》明确提供“等待所有流水线操作完成。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《asc_sync（同步）》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》明确提供“DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscSyncPipe](asc_sync_pipe.md)（`related`）：AscSyncPipe 只等待指定流水，asc_sync 等待所有流水；可按依赖范围选择精细屏障或全局完成。
- [AscSyncWait](asc_sync_wait.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncWait》明确提供“等待特定的同步标志，阻塞当前流水线直到条件满足，与asc_sync_notify配对使用。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [同步控制](sync_control.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《同步控制》明确提供“SIMD C API同步控制类接口汇总，提供lock、sync、barrier、notify等多级同步与锁机制。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [核内同步能力概述](intra_core_sync_overview.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《核内同步能力概述》明确提供“AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscAbsSync](../deprecated_interface/asc_abs_sync_deprecated.md)（`same_topic`）：《AscAbsSync》处理“已废弃的按元素取绝对值同步计算接口，请改用asc_abs和asc_sync实现精细化调优。”。《asc_sync（同步）》提供“等待所有流水线操作完成。”，其具体合同或探针直接接入废弃 AscAbsSync 拆分为 AscAbs 与 asc_sync 的迁移合同。
- [AscSyncDataBarrier](asc_sync_data_barrier.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《asc_sync（同步）》提供“等待所有流水线操作完成。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [AscSyncMte2](asc_sync_mte2.md)（`same_topic`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncMte2》明确提供“针对PIPE_MTE2流水线执行同步操作，保证其前序指令全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能执行。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscSyncMte3](asc_sync_mte3.md)（`same_topic`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncMte3》明确提供“针对PIPE_MTE3流水线执行同步操作，保证其前序指令全部完成后，PIPE_MTE2与PIPE_V流水线的后续指令才能执行。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscSyncVec](asc_sync_vec.md)（`same_topic`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncVec》明确提供“针对PIPE_V流水线执行同步操作。无入参函数原型已废弃，请使用asc_sync执行所有流水线的同步。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
<!-- cannbot:related:end -->
