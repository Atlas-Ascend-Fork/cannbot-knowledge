---
type: API
title: GetSubBlockNum
description: 在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSubBlockNum_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetSubBlockNum

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

在分离模式架构下，获取当前配置中，一个逻辑AI Core上Cube Core（AIC）或者Vector Core（AIV）的数量。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetSubBlockIdx](../../../adv_api/cube_compute/matmul_kernel/get_sub_block_idx.md)（`related`）：GetSubBlockIdx 与《GetSubBlockNum》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [AscGetSubBlockId](../../../c_api/sys_var/asc_get_sub_block_id.md)（`same_topic`）：AscGetSubBlockId 与《GetSubBlockNum》的实质衔接是：AscGetSubBlockId 返回分离架构 AIV 组内 ID，C++ GetSubBlockIdx 是对应查询，SubBlockNum 给出编号上界，SetSubBlockIdx 可覆盖 ID；双 AIV 故障及 arrive/wait 说明该 ID 如何选择同步 flag 段。
- [AscGetSubBlockNum](../../../c_api/sys_var/asc_get_sub_block_num.md)（`same_topic`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockNum》说明在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [GetSubBlockIdx](get_sub_block_idx_isasi.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《GetSubBlockNum》明确“在分离模式架构下，获取一个逻辑AI Core上AIC或AIV的数量。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
<!-- cannbot:related:end -->
