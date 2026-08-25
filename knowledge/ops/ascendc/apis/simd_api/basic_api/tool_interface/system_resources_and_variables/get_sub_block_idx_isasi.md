---
type: API
title: GetSubBlockIdx
description: 在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSubBlockIdx_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetSubBlockIdx

头文件路径为： "basic_api/kernel_operator_sys_var_intf.h"。

在分离模式架构下，获取逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的逻辑索引。

GetSubBlockIdx在使用__mix__(1, 2)作为函数执行空间限定符的场景下，可以用于区分同一个核上的两个不同Vector Core，取值分别为0和1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《双AIV CrossCoreFlag 的 subBlock 契约缺陷》明确“Ascend950 双 AIV 融合 kernel 中，AIC 为 V0/V1 设置不同 flag 段，而 AIV wait 未按 subBlock 偏移，且空分支可能不回传 flag；源码依赖图可确认同步缺陷，但单独修正后 507015 仍存在，不能把整起异常只归因于该缺陷。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
- [AscGetSubBlockNum](../../../c_api/sys_var/asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockIdx》说明在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscGetSubBlockId](../../../c_api/sys_var/asc_get_sub_block_id.md)（`same_topic`）：AscGetSubBlockId 与《GetSubBlockIdx》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [GetSubBlockIdx](../../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《GetSubBlockIdx》明确“获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
- [GetSubBlockNum](get_sub_block_num_isasi.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《GetSubBlockNum》明确“在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
- [SetSubBlockIdx](../../../adv_api/cube_compute/matmul_kernel/set_sub_block_idx.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《SetSubBlockIdx》明确“设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
<!-- cannbot:related:end -->
