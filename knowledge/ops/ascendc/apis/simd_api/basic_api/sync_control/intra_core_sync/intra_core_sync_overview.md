---
type: API
title: 核内同步能力概述
description: AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 核内同步能力概述

AI Core 内部的执行单元（如 MTE2 搬运单元、Vector 计算单元等）以异步并行方式运行，在读写同一存储资源时可能存在数据依赖关系，需通过同步控制协调操作时序确保数据一致性。
硬件流水类型包括 PIPE_S（标量）、PIPE_V（矢量）、PIPE_M（矩阵）、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX 等。
核内同步分为两类：多流水同步用于不同类型流水间的依赖控制，通过 SetFlag/WaitFlag 或 Lock/Unlock 接口实现；单流水同步用于相同类型流水间的顺序控制，通过 PipeBarrier 接口实现。
Ascend 950PR/950DT 新增 Lock/Unlock 接口，相比 SetFlag/WaitFlag 内聚性更强且支持更多同步信号量。
TPipe-TQue 框架和毕昇编译器支持自动同步，部分场景仍需开发者手动插入同步。

<!-- cannbot:related:start -->
## 相关

- [LocalMemBar](../../reg_vector_compute/sync_control/local_mem_bar.md)（`related`）：LocalMemBar 与《核内同步能力概述》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [系统同步能力概述（同步控制）](../system_sync_overview.md)（`related`）：系统同步能力概述（同步控制） 与《核内同步能力概述》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
- [DataSyncBarrier](data_sync_barrier_isasi.md)（`same_topic`）：概览解释 DataSyncBarrier、PipeBarrier 和 event 的同步范围，防止用过强/过弱屏障。
- [Lock](lock.md)（`same_topic`）：Lock 与《核内同步能力概述》的实质衔接是：Lock 必须用 AllocMutexID 得到 mutex，并与 Unlock、ReleaseMutexID 成对；C Lock/Unlock 和核内同步概述共享同一阻塞流水契约。
- [PipeBarrier](pipe_barrier_isasi.md)（`same_topic`）：概览解释 barrier、event、mutex 的作用域。
- [ReleaseMutexID](release_mutex_id_isasi.md)（`same_topic`）：ReleaseMutexID 与《核内同步能力概述》的实质衔接是：ReleaseMutexID 必须在 Lock/Unlock 完成后与 AllocMutexID 成对，避免框架 mutex 资源耗尽；C Lock/Unlock 是同一资源契约的对应入口。
- [关键特性说明](key_features.md)（`same_topic`）：概览解释 key features 中 event、barrier、mutex 的同步域和适用条件。
- [核内同步](intra_core_sync.md)（`same_topic`）：核内同步 与《核内同步能力概述》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [核内同步能力概述](../../../c_api/sync/intra_core_sync_overview.md)（`same_topic`）：Basic API 概述按跨流水、同流水和 Scalar 内存依赖分类同步机制，可与 C API 名称映射并完成机制选型。
<!-- cannbot:related:end -->
