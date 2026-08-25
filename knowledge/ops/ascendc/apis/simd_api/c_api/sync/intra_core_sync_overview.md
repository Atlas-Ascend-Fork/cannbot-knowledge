---
type: API
title: 核内同步能力概述
description: AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/intra_core_sync_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 核内同步能力概述

AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。硬件流水类型包括PIPE_S（标量）、PIPE_V（矢量计算）、PIPE_M（矩阵计算）、PIPE_MTE1（L1到L0搬运）、PIPE_MTE2（GM到L1/UB搬运）、PIPE_MTE3（UB到GM搬运）、PIPE_FIX（L0C到GM搬运）。

核内同步分为多流水同步和单流水同步：多流水同步通过asc_sync_notify/asc_sync_wait或asc_lock/asc_unlock接口控制不同类型流水间的依赖；单流水同步通过asc_sync_pipe接口保证同一流水内前序指令完成后才执行后续指令。asc_sync_data_barrier接口可阻塞后续指令直到此前内存访问全部完成。

<!-- cannbot:related:start -->
## 相关

- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：该排障卡用 MTE2→Scalar→MTE3 数据链具体说明事件只覆盖硬件 pipe、Scalar 访问还需显式可见性处理，补足概述到诊断的桥梁。
- [AscSyncIntraArrive](asc_sync_intra_arrive.md)（`related`）：《AscSyncIntraArrive》处理“与asc_sync_intra_wait配合使用，用于block内不同Core的流水线同步，向同步寄存器发送同步信号。”。《核内同步能力概述》明确“AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。”，可直接用于核对核内 arrive/wait 配对、可见性范围及双 AIV flag 路由缺陷。
- [TQueSync](../../basic_api/sync_control/intra_core_sync/t_que_sync_template_params.md)（`related`）：TQueSync 将源/目的流水编码为模板参数并配合 SetFlag/WaitFlag，提供跨硬件版本兼容的依赖表达，补充 C API 原语的选型依据。
- [asc_sync（同步）](asc_sync.md)（`related`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《核内同步能力概述》明确提供“AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写同一存储资源时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
- [AscSyncMte3](asc_sync_mte3.md)（`same_topic`）：AscSyncMte3 与《核内同步能力概述》的实质衔接是：AscSyncMte3 与 MTE2/Vector/pipe/barrier 配套，保证 MTE3 写出在消费者读取前完成。
- [AscSyncWait](asc_sync_wait.md)（`same_topic`）：AscSyncWait 与《核内同步能力概述》的实质衔接是：AscSyncWait 与 AscSyncNotify 是同一事件的等待/通知对，核内同步概述解释 event id 与流水依赖。
- [核内同步](../../basic_api/sync_control/intra_core_sync/intra_core_sync.md)（`same_topic`）：核内同步 与《核内同步能力概述》的实质衔接是：核内同步的选择取决于流水依赖：MTE 事件用 SetFlag/WaitFlag，指令流水用 PipeBarrier，mutex 用 Lock；所连案例验证错误枚举、缺失屏障和跨 VF 可见性。
- [核内同步能力概述](../../basic_api/sync_control/intra_core_sync/intra_core_sync_overview.md)（`same_topic`）：Basic API 概述按跨流水、同流水和 Scalar 内存依赖分类同步机制，可与 C API 名称映射并完成机制选型。
<!-- cannbot:related:end -->
