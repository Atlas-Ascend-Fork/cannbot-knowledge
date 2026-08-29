---
type: API
title: 任务间同步
description: 任务间同步接口索引页，包含SetNextTaskStart与WaitPreTaskEnd。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_task_sync/inter_task_sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 任务间同步

提供 SetNextTaskStart 和 WaitPreTaskEnd 接口，用于 SuperKernel 特性的 Early-Start 能力。SetNextTaskStart 在子 Kernel 中调用后，后续指令可与后续子 Kernel 并行执行；WaitPreTaskEnd 调用前的指令可与前序子 Kernel 并行。

SuperKernel 是算子二进制融合技术，通过融合多个子 Kernel 减少任务调度开销。开发者需自行保证调用后指令不会与后序算子互相干扰，推荐在算子最后一条搬运指令后调用。SetNextTaskStart 为试验接口，仅 Ascend 950PR/950DT 和 Atlas A3 系列实际生效，其他产品仅保证编译兼容。
