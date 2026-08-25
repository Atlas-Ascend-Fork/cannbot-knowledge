---
type: API
title: 核内同步
description: 核内同步接口索引页，汇总TQueSync模板参数、SetFlag/WaitFlag、PipeBarrier、DataSyncBarrier、Mutex及Lock/Unlock等。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核内同步

核内同步接口协调同一核内不同流水线之间的执行顺序。SetFlag/WaitFlag及ISASI变体实现多流水线同步，SetFlag发送通知，WaitFlag阻塞等待。
PipeBarrier(ISASI)实现单流水线内指令同步（不支持PIPE_S）；DataSyncBarrier(ISASI)阻塞后续指令直到此前内存访问完成。Lock/Unlock提供流水线锁机制，Mutex(ISASI)封装互斥操作。AllocMutexID/ReleaseMutexID(ISASI)用于分配和释放互斥ID。TQueSync模板参数用于配置队列同步属性。

<!-- cannbot:related:start -->
## 相关

- [PipeBarrier 的 PIPE_V 是全局枚举](../../../../../runbooks/compilation/pipebarrier_pipe_v_uses_global_enum.md)（`exemplifies`）：核内同步 与《PipeBarrier 的 PIPE_V 是全局枚举》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线](../../../../../runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)（`exemplifies`）：核内同步 与《PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`exemplifies`）：核内同步 与《Reg 固定地址跨块累加需逐 VF PipeBarrier》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：核内同步 与《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [LocalMemBar](../../reg_vector_compute/sync_control/local_mem_bar.md)（`related`）：LocalMemBar 与《核内同步》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [Lock](lock.md)（`same_topic`）：Lock 与《核内同步》的实质衔接是：Lock 必须用 AllocMutexID 得到 mutex，并与 Unlock、ReleaseMutexID 成对；C Lock/Unlock 和核内同步概述共享同一阻塞流水契约。
- [ReleaseMutexID](release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《核内同步》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：核内同步 与《核内同步能力概述》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [核内同步能力概述](../../../c_api/sync/intra_core_sync_overview.md)（`same_topic`）：核内同步 与《核内同步能力概述》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
<!-- cannbot:related:end -->
