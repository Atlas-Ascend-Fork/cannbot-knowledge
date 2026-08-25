---
type: API
title: AscSyncMte2
description: 针对PIPE_MTE2流水线执行同步操作，保证其前序指令全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能执行。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_mte2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncMte2

针对PIPE_MTE2流水线执行同步操作。其作用是保证PIPE_MTE2流水线中前序指令（如GM到UB的数据搬运）全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能开始执行。
函数原型：void asc_sync_mte2(int id)
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：Runbook 用带宽探针验证 kernel 末尾必须等待 MTE2/MTE3 工作完成，host stream sync 不能替代 kernel 内流水同步；它补充了接口的测量与退出边界。
- [AscSyncMte3](asc_sync_mte3.md)（`related`）：AscSyncMte2 保证 MTE2 前序完成后 MTE3/V 才继续，AscSyncMte3 则保证搬出完成后 MTE2/V 继续；二者按生产者流水方向成对选用。
- [AscSyncPipe](asc_sync_pipe.md)（`related`）：地址重叠的 MTE2 搬入依赖可用专用 AscSyncMte2 约束其完成后再启动 MTE3/V，比泛化 pipe 参数更明确。
- [asc_sync（同步）](asc_sync.md)（`same_topic`）：《asc_sync（同步）》处理“等待所有流水线操作完成。”。《AscSyncMte2》明确提供“针对PIPE_MTE2流水线执行同步操作，保证其前序指令全部完成后，PIPE_MTE3与PIPE_V流水线的后续指令才能执行。”，其参数、调用或验证步骤直接接入等待全部流水的 sync_all/pipe/barrier 入口与实际 MTE/队列 hazard 验证。
<!-- cannbot:related:end -->
