---
type: API
title: AscSyncBlockWait
description: 与asc_sync_block_arrive配合使用，等待所有同步对象到达flag_id对应的同步点后解除阻塞。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_block_wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncBlockWait

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。组内block和subblock间同步指同一group内block（AIC）与subblock（AIV）之间的同步。 和asc_sync_block_arrive配合使用（通过flag_id关联），用于等待所有同步对象到达flag_id对应的同步点。如果flag_id所对应的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。
函数原型：void asc_sync_block_wait(pipe_t pipe, uint8_t flag_id)
约束：flag_id的取值范围为0至15，每个flag_id的计数器范围为0至15。；必须保证每个flag_id的四位计数器不溢出，否则将引发异常。；必须保证相同的flag_id在同一时间仅被一条流水线使用。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscSyncInterWait](asc_sync_inter_wait.md)（`related`）：BlockWait 等待组内 block/subblock 全部到达，而 InterWait 等待不同 group 的信号；二者提供不同层级的 barrier/notification 选择。
- [AscSyncSubblockWait](asc_sync_subblock_wait.md)（`related`）：SubblockWait 只同步同组不同 AIV subblock，而 BlockWait 同步主 block 与 subblock；对比作用域可避免在 1:N 分离模式中选错等待原语。
- [AscSyncBlockArrive](asc_sync_block_arrive.md)（`same_topic`）：AscSyncBlockArrive 增加 block 同步计数，AscSyncBlockWait 等待该计数满足条件，二者构成同一 block 同步协议的到达/等待两端。
<!-- cannbot:related:end -->
