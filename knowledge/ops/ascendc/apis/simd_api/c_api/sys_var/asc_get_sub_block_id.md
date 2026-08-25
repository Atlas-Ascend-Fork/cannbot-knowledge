---
type: API
title: AscGetSubBlockId
description: 获取AI Core上Vector核的ID。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_sub_block_id.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetSubBlockId

获取AI Core上Vector核的ID。
函数原型：int64_t asc_get_sub_block_id()
返回值：返回Vector核ID。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：AscGetSubBlockId 与《双AIV CrossCoreFlag 的 subBlock 契约缺陷》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [AscGetSubBlockNum](asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscGetSubBlockId》说明获取AI Core上Vector核的ID。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncSubblockArrive](../sync/asc_sync_subblock_arrive.md)（`related`）：AscGetSubBlockId 与《AscSyncSubblockArrive》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [AscSyncSubblockWait](../sync/asc_sync_subblock_wait.md)（`related`）：AscGetSubBlockId 与《AscSyncSubblockWait》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [GetSubBlockIdx](../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`related`）：GetSubBlockIdx 与《AscGetSubBlockId》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [GetSubBlockIdx](../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_idx_isasi.md)（`same_topic`）：AscGetSubBlockId 与《GetSubBlockIdx》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [GetSubBlockNum](../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_num_isasi.md)（`same_topic`）：AscGetSubBlockId 与《GetSubBlockNum》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [SetSubBlockIdx](../../adv_api/cube_compute/matmul_kernel/set_sub_block_idx.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《AscGetSubBlockId》补充：获取AI Core上Vector核的ID。
<!-- cannbot:related:end -->
