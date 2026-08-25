---
type: API
title: AscSyncBlockArrive
description: 与asc_sync_block_wait配合使用，通过flag_id关联，用于组内block和subblock间的信号同步。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_block_arrive.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncBlockArrive

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。组内block和subblock间同步指同一group内block（AIC）与subblock（AIV）之间的同步。 和asc_sync_block_wait配合使用（通过flag_id关联），用于组内block和subblock间的信号同步。通过向核间同步寄存器发送同步信号，标识当前pipeline已到达flag_id对应的同步点。每个flag_id对应一个初始值为0的计数器，执行asc_sync_block_arrive后flag_id对应的计数器增加1；执行asc_sync_block_wait时如果对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。
函数原型：void asc_sync_block_arrive(pipe_t pipe, int64_t flag_id)
约束：使用该同步接口时，需要按照如下规则设置Kernel类型：；在纯Vector/Cube场景下，需设置Kernel类型为KERNEL_TYPE_MIX_AIV_1_0或KERNEL_TYPE_MIX_AIC_1_0。；对于Vector和Cube混合场景，需根据实际情况灵活配置Kernel类型。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSyncBlockWait](asc_sync_block_wait.md)（`same_topic`）：AscSyncBlockArrive 增加 block 同步计数，AscSyncBlockWait 等待该计数满足条件，二者构成同一 block 同步协议的到达/等待两端。
<!-- cannbot:related:end -->
