---
type: API
title: SetSubBlockIdx
description: 设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0,
  1, ..., N-1。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSubBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetSubBlockIdx

设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。

函数原型：__aicore__ inline void SetSubBlockIdx(uint8_t subBlockIdx)

参数：
- subBlockIdx（输入）：当前AIV核的ID。

约束：
- 该接口仅支持在分离架构下使用。
- 在分离架构中，AIV核的ID会在REGIST_MATMUL_OBJ()接口内部自动初始化和赋值。如果在算子程序中使用了REGIST_MATMUL_OBJ()接口，则不建议调用此接口；若未使用REGIST_MATMUL_OBJ\(\)接口，则请调用此接口并将子核ID设置为0。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《双AIV CrossCoreFlag 的 subBlock 契约缺陷》补充：Ascend950 双 AIV 融合 kernel 中，AIC 为 V0/V1 设置不同 flag 段，而 AIV wait 未按 subBlock 偏移，且空分支可能不回传 flag；源码依赖图可确认同步缺陷，但单独修正后 507015 仍存在，不能把整起异常只归因于该缺陷。
- [AscGetSubBlockNum](../../../c_api/sys_var/asc_get_sub_block_num.md)（`related`）：《AscGetSubBlockNum》说明分离模式下获取一个AI Core上Cube或Vector核的数量。；《SetSubBlockIdx》说明设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。。二者在subBlock数量和编号共同定位AIV子块，SetSubBlockIdx、子块同步及CrossCoreFlag故障直接依赖这套系统变量合同上存在可执行的直接衔接。
- [AscSyncSubblockArrive](../../../c_api/sync/asc_sync_subblock_arrive.md)（`related`）：AscSyncSubblockArrive 与《SetSubBlockIdx》的实质衔接是：SubblockArrive 必须与 SubblockWait 配对并正确取得 subblock ID；双 AIV 故障卡验证了这一 flag 计数契约。
- [Matmul使用说明](matmul_usage.md)（`related`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《Matmul使用说明》补充：Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。
- [AscGetSubBlockId](../../../c_api/sys_var/asc_get_sub_block_id.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《AscGetSubBlockId》补充：获取AI Core上Vector核的ID。
- [GetSubBlockIdx](get_sub_block_idx.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《GetSubBlockIdx》补充：获取当前AIV核在当前AI Core分组中的ID，需在REGIST_MATMUL_OBJ之后调用。仅分离架构支持。
- [GetSubBlockIdx](../../../basic_api/tool_interface/system_resources_and_variables/get_sub_block_idx_isasi.md)（`same_topic`）：《GetSubBlockIdx》处理“在分离模式架构下，获取逻辑AI Core上AIC或AIV的逻辑索引。”。《SetSubBlockIdx》明确“设置当前AIV核的ID。分离架构下，一个AI Core由Cube Core（AIC）和Vector Core（AIV）按照一定比例1：N进行组合，其中N个AIV核的ID分别为0, 1, ..., N-1。”，可直接用于核对双 AIV subBlock 索引/数量的 C/C++ 入口、显式设置和同步缺陷验证。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《REGIST_MATMUL_OBJ》补充：初始化Matmul对象。
<!-- cannbot:related:end -->
