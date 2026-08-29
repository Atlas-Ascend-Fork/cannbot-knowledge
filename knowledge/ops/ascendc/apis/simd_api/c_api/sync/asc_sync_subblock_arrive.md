---
type: API
title: AscSyncSubblockArrive
description: 与asc_sync_subblock_wait配合使用，通过flag_id关联，用于组内不同subblock间的信号同步。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_subblock_arrive.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncSubblockArrive

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。组内subblock间同步指同一group内不同subblock（AIV）之间的同步。 和asc_sync_subblock_wait配合使用（通过flag_id关联），用于组内subblock间的信号同步。通过向核间同步寄存器发送同步信号，标识当前pipeline已到达flag_id对应的同步点。每个flag_id对应一个初始值为0的计数器，执行asc_sync_subblock_arrive后flag_id对应的计数器增加1；执行asc_sync_subblock_wait时如果对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。
函数原型：void asc_sync_subblock_arrive(pipe_t pipe, int64_t flag_id)
约束：不建议开发者同时使用该接口和Matmul高阶API，否则会有flag_id冲突的风险。；同一flag_id的计数器最多设置15次。；必须保证配套使用asc_sync_subblock_arrive和asc_sync_subblock_wait，否则会出现未定义行为。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSyncSubblockWait](asc_sync_subblock_wait.md)（`same_topic`）：必须保证配套使用asc_sync_subblock_arrive和asc_sync_subblock_wait，否则会出现未定义行为。；执行asc_sync_subblock_wait时如果对应的计数器数值为0则阻塞；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。；arrive 负责递增 flag_id 计数器并明确要求与 wait 配套，wait 负责在相同计数器上阻塞和消费一次到达信号，是同一 subblock 同步握手的两端。
<!-- cannbot:related:end -->
