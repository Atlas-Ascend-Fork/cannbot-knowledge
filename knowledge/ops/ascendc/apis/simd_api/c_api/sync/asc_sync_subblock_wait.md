---
type: API
title: AscSyncSubblockWait
description: 与asc_sync_subblock_arrive配合使用，等待组内subblock到达flag_id对应的同步点后解除阻塞。
tags: [task.lookup, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_sync_subblock_wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSyncSubblockWait

在分离模式下，AIC（Cube Core）与AIV（Vector Core）按group划分，一个group由1个block（主核）和N个subblock（从核）组成，比例1:N。组内subblock间同步指同一group内不同subblock（AIV）之间的同步。 核间同步指令，每个flag_id均分配有计数器，执行asc_sync_subblock_arrive后计数器将递增；执行asc_sync_subblock_wait时如果对应的计数器数值为0则阻塞；如果对应的计数器大于0，则计数器减一，同时后续指令开始执行。
函数原型：void asc_sync_subblock_wait(pipe_t pipe, uint8_t flag_id)
约束：flag_id的取值范围为0至15，每个flag_id的计数器范围为0至15。；必须保证每个flag_id的计数器不溢出，否则将引发异常。；必须保证相同的ID在同一时间仅被一条流水线等待。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：Runbook 给出双 AIV subBlock 身份/flag 契约错误导致 507015 的实测，补充 Wait/Arrive 抽象计数器之外的分离模式排障。
- [AscGetSubBlockId](../sys_var/asc_get_sub_block_id.md)（`related`）：AscGetSubBlockId 与《AscSyncSubblockWait》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [AscGetSubBlockNum](../sys_var/asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscSyncSubblockWait》说明与asc_sync_subblock_arrive配合使用，等待组内subblock到达flag_id对应的同步点后解除阻塞。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncBlockWait](asc_sync_block_wait.md)（`related`）：SubblockWait 只同步同组不同 AIV subblock，而 BlockWait 同步主 block 与 subblock；对比作用域可避免在 1:N 分离模式中选错等待原语。
- [AscSyncSubblockArrive](asc_sync_subblock_arrive.md)（`same_topic`）：AscSyncSubblockArrive 与《AscSyncSubblockWait》的实质衔接是：SubblockArrive 必须与 SubblockWait 配对并正确取得 subblock ID；双 AIV 故障卡验证了这一 flag 计数契约。
<!-- cannbot:related:end -->
