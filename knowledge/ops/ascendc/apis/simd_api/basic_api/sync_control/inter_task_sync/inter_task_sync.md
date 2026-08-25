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

<!-- cannbot:related:start -->
## 相关

- [SK_BIND（SuperKernel）](../../../../utils_api/super_kernel/sk_bind.md)（`related`）：SK_BIND（SuperKernel） 与《任务间同步》的实质衔接是：SK_BIND 绑定 SuperKernel 子任务，需结合 kernel 类型/tiling、前后任务同步和 runtime context。
- [同步控制](../../../c_api/sync/sync_control.md)（`related`）：同步控制 与《任务间同步》的实质衔接是：该同步总览按核内、核间、任务间和 SIMT fence 划分选择，所选卡解释这些同步域的边界。
- [系统同步能力概述（同步控制）](../system_sync_overview.md)（`related`）：系统同步能力概述（同步控制） 与《任务间同步》的实质衔接是：系统同步能力按核内、核间、任务间分层；这些概述提供选择同步域所需的边界，而非把所有同步 API 机械串联。
- [SetNextTaskStart](set_next_task_start.md)（`same_topic`）：任务间同步总页给出 set/wait 的配对顺序和适用流水，是单接口的完整契约。
- [WaitPreTaskEnd](wait_pre_task_end.md)（`same_topic`）：WaitPreTaskEnd 与《任务间同步》的实质衔接是：WaitPreTaskEnd 与 SetNextTaskStart 构成前后任务的早启动握手；任务间同步和 SuperKernel 卡解释该握手在绑定任务调度中的生效条件。
<!-- cannbot:related:end -->
