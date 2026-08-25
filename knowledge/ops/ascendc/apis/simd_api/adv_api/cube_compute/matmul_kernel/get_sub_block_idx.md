---
type: API
title: GetSubBlockIdx
description: 获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetSubBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetSubBlockIdx

获取当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV的子核ID分别为0, 1, ..., N-1。 Matmul::GetSubBlockIdx()与基础API接口AscendC::GetSubBlockIdx()的区别在于，Matmul::GetSubBlockIdx()用于获取当前AIV核在当前AI Core分组中的ID，而AscendC::GetSubBlockIdx\(\)获取的是AIV核在所有AI Core分组中的逻辑ID。

函数原型：__aicore__ inline uint8_t GetSubBlockIdx()

返回值：当前AIV核的ID。

约束：
- 该接口仅支持在分离架构下使用，否则返回随机值。
- 在分离架构中，AIV核的ID会在REGIST_MATMUL_OBJ()接口内部自动初始化和赋值。因此，需要在调用REGIST_MATMUL_OBJ()接口之后，再调用本接口，以获取正确的ID。
- 若在算子程序中调用SetSubBlockIdx()后， GetSubBlockIdx()接口将返回由SetSubBlockIdx接口设置的ID值。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：GetSubBlockIdx 与《双AIV CrossCoreFlag 的 subBlock 契约缺陷》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [AscGetBlockIdx](../../../c_api/sys_var/asc_get_block_idx.md)（`related`）：GetSubBlockIdx 与《AscGetBlockIdx》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [AscGetSubBlockId](../../../c_api/sys_var/asc_get_sub_block_id.md)（`related`）：GetSubBlockIdx 与《AscGetSubBlockId》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [AscGetSubBlockNum](../../../c_api/sys_var/asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《GetSubBlockIdx》说明获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncSubblockArrive](../../../c_api/sync/asc_sync_subblock_arrive.md)（`related`）：AscSyncSubblockArrive 与《GetSubBlockIdx》的实质衔接是：SubblockArrive 必须与 SubblockWait 配对并正确取得 subblock ID；双 AIV 故障卡验证了这一 flag 计数契约。
- [GetBlockIdx](../../../basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`related`）：GetSubBlockIdx 与《GetBlockIdx》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [GetSubBlockNum](../../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_num_isasi.md)（`related`）：GetSubBlockIdx 与《GetSubBlockNum》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`related`）：GetSubBlockIdx 与《REGIST_MATMUL_OBJ》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [GetSubBlockIdx](../../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_idx_isasi.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《GetSubBlockIdx》明确“获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
- [SetSubBlockIdx](set_sub_block_idx.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《GetSubBlockIdx》补充：获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。
<!-- cannbot:related:end -->
