---
type: API
title: 核间同步
description: 核间同步接口索引页，汇总IBSet、IBWait、SyncAll、CrossCoreSetFlag/WaitFlag(ISASI)及NotifyNextBlock/WaitPreBlock。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/inter_core_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 核间同步

核间同步接口协调多个AIC/AIV核之间的执行顺序。硬件同步类接口包括CrossCoreSetFlag/CrossCoreWaitFlag(ISASI)和SyncAll，前者负责通知与阻塞等待，后者支持纯Vector全核同步和融合算子三阶段同步。
软件同步类接口包括IBSet/IBWait（全局内存信号量轮询）和SyncAll的软件模式。InitDetermineComputeWorkspace/NotifyNextBlock/WaitPreBlock三者组合使用，确保多AIV核按blockIdx升序执行，适用于确定性计算场景。

<!-- cannbot:related:start -->
## 相关

- [A5 mix(1,2) mode=2 漏 AIV1 flag 致全零](../../../../../runbooks/precision/a5_mix_1_2_mode_2_aiv1_flag.md)（`exemplifies`）：CrossCore 模式还受 AIC:AIV 拓扑约束；双 AIV 下沿用 mode=2 会漏给 AIV1 路由 flag，补充模式选型边界。
- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：核间同步总览列出 CrossCore flag 路线；该 runbook 证明 set/wait 方向和 flag 配对错误会使通算流水死锁。
- [核间负载均衡](../../../../../guides/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md)（`explains`）：核间负载均衡 与《核间同步》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《核间同步》补充：核间同步接口索引页，汇总IBSet、IBWait、SyncAll、CrossCoreSetFlag/WaitFlag(ISASI)及NotifyNextBlock/WaitPreBlock。
- [SyncAll](sync_all.md)（`same_topic`）：核间同步接口页汇总 SyncAll 及信号式替代方案，便于按全局屏障或点对点依赖选型。
<!-- cannbot:related:end -->
