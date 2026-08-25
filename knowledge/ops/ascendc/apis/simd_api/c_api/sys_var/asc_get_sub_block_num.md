---
type: API
title: AscGetSubBlockNum
description: 分离模式下获取一个AI Core上Cube或Vector核的数量。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_sub_block_num.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetSubBlockNum

分离模式下，获取一个AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。
函数原型：int64_t asc_get_sub_block_num()
返回值：不同Kernel类型下，在AIC和AIV上调用该接口的返回值如下：
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《双AIV CrossCoreFlag 的 subBlock 契约缺陷》说明Ascend950 双 AIV 融合 kernel 中，AIC 为 V0/V1 设置不同 flag 段，而 AIV wait 未按 subBlock 偏移，且空分支可能不回传 flag；源码依赖图可确认同步缺陷，但单独修正后 507015 仍存在，不能把整起异常只归因于该缺陷。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscGetBlockNum](asc_get_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscGetBlockNum》说明获取当前任务配置的核数，用于多核逻辑控制。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscGetSubBlockId](asc_get_sub_block_id.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscGetSubBlockId》说明获取AI Core上Vector核的ID。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncSubblockArrive](../sync/asc_sync_subblock_arrive.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscSyncSubblockArrive》说明与asc_sync_subblock_wait配合使用，通过flag_id关联，用于组内不同subblock间的信号同步。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncSubblockWait](../sync/asc_sync_subblock_wait.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《AscSyncSubblockWait》说明与asc_sync_subblock_arrive配合使用，等待组内subblock到达flag_id对应的同步点后解除阻塞。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [GetSubBlockIdx](../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockIdx》说明获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [GetSubBlockIdx](../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_idx_isasi.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockIdx》说明在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [SetSubBlockIdx](../../adv_api/cube_compute/matmul_kernel/set_sub_block_idx.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《SetSubBlockIdx》说明设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [系统变量](system_variables.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《系统变量》说明SIMD C API系统变量类接口汇总，提供架构版本、核编号、循环计数器、CTRL寄存器等系统变量的查询与设置。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [GetSubBlockNum](../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_num_isasi.md)（`same_topic`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockNum》说明在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
