---
type: API
title: AscSyncPipe
description: 完成同一流水线内的同步控制，保证前序指令的所有数据读写完成后，后序指令才能开始执行。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_pipe.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncPipe

完成同一流水线内的同步控制，用于在同一流水线内部约束执行顺序。如图1所示，其作用是保证指定流水线中前序指令的所有数据读写全部完成后，该流水线的后序指令才能开始执行。 图1  asc_sync_pipe接口功能示意图
函数原型：void asc_sync_pipe(pipe_t pipe)
约束：Scalar流水之间的同步由硬件自动保证，asc_sync_pipe接口不支持PIPE_S单流水的同步。；asc_sync_pipe(PIPE_ALL)会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅阻塞单条流水线即可解决问题，应避免随意调用asc_sync_pipe(PIPE_ALL)。；PIPE_MTE2/PIPE_MTE3在搬运地址有重叠的情况下需要开发者插入同步。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSyncMte2](asc_sync_mte2.md)（`related`）：地址重叠的 MTE2 搬入依赖可用专用 AscSyncMte2 约束其完成后再启动 MTE3/V，比泛化 pipe 参数更明确。
- [PipeBarrier](../../basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)（`related`）：PipeBarrier 是 C++ 基础 API 的同流水同步对应，同样不支持 PIPE_S 并建议只阻塞必要管线。
- [asc_sync（同步）](asc_sync.md)（`related`）：AscSyncPipe 只等待指定流水，asc_sync 等待所有流水；可按依赖范围选择精细屏障或全局完成。
<!-- cannbot:related:end -->
