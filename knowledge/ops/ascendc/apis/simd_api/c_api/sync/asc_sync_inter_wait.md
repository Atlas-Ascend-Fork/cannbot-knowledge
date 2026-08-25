---
type: API
title: AscSyncInterWait
description: 与asc_sync_inter_arrive配合使用，等待组间block到达flag_id对应的同步点后解除阻塞。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_inter_wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncInterWait

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。组间同步指不同group之间的同步，即所有block（所有AIC或所有AIV）之间的同步。 核间同步指令，与asc_sync_inter_arrive配合使用（通过flag_id关联），用于组间block的信号同步。 每个flag_id均分配有计数器，执行asc_sync_inter_arrive后计数器将递增；执行asc_sync_inter_wait时如果对应的计数器数值为0则阻塞；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。
函数原型：void asc_sync_inter_wait(pipe_t pipe, uint8_t flag_id)
约束：flag_id的取值范围为0至15，每个flag_id的计数器范围为0至15。；必须保证每个flag_id的计数器不溢出，否则将引发异常。；必须保证相同的ID在同一时间仅被一条流水线等待。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSyncBlockWait](asc_sync_block_wait.md)（`related`）：BlockWait 等待组内 block/subblock 全部到达，而 InterWait 等待不同 group 的信号；二者提供不同层级的 barrier/notification 选择。
- [AscSyncIntraWait](asc_sync_intra_wait.md)（`related`）：IntraWait 与 InterWait 都是阻塞等待，但作用域分别为 block 内不同 Core 与不同 group；可用作用域差异避免把 inter 同步误用于核内流水。
- [AscSyncInterArrive](asc_sync_inter_arrive.md)（`same_topic`）：asc_sync_inter_wait 必须由另一 group 的 asc_sync_inter_arrive 使用同一 flag_id 发出信号；两者是不可拆分的跨 group 同步握手。
<!-- cannbot:related:end -->
