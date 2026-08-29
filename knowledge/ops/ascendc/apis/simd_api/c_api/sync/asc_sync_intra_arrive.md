---
type: API
title: AscSyncIntraArrive
description: 与asc_sync_intra_wait配合使用，用于block内不同Core的流水线同步，向同步寄存器发送同步信号。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_intra_arrive.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSyncIntraArrive

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。block内同步指同一block内block（AIC）与单个subblock（AIV）之间的同步。 block内同步指令，与asc_sync_intra_wait配合使用，是block内不同Core的流水线同步指令，用于向每个Core的同步寄存器发送同步信号。每个sync_id对应Vector Core与Cube Core中的一个初始值为0的计数器。asc_sync_intra_arrive指令后其他Core对应的计数器增加1；执行asc_sync_intra_wait时如果对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。 block内同步场景可细分为两类：
函数原型：void asc_sync_intra_arrive(pipe_t pipe, uint8_t sync_id)
约束：需要保证每一个ID的计数器不会溢出，否则会出现异常。；需要保证相同的ID只会被一个流水线控制。；每个ID对应一个计数器，特定CORE的同步ID计数器可通过其他CORE发起的asc_sync_intra_arrive递增；也可通过本身发起的asc_sync_intra_wait递减。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSyncIntraWait](asc_sync_intra_wait.md)（`related`）：asc_sync_intra_arrive指令后其他Core对应的计数器增加1；执行asc_sync_intra_wait时如果对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。；asc_sync_intra_arrive指令后其他CORE对应的计数器增加1；执行asc_sync_intra_wait时如果对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。；arrive 负责增加另一 Core 的 sync_id 计数，wait 依据同一计数阻塞或消费一次信号，两端共同定义 block 内流水同步的成对调用协议。
<!-- cannbot:related:end -->
