---
type: API
title: InterHcclGroupSync
description: 用于等待一个跨通信域的通信任务完成。调用该接口后，本通信域后续下发的通信任务，均等待指定的srcGroupID通信域中的srcHandleID通信任务执行完成，才开始执行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/InterHcclGroupSync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a3]
---

# InterHcclGroupSync

用于等待一个跨通信域的通信任务完成。调用该接口后，本通信域后续下发的通信任务，均等待指定的srcGroupID通信域中的srcHandleID通信任务执行完成，才开始执行。

函数原型：__aicore__ inline void InterHcclGroupSync(int8_t srcGroupID, HcclHandle srcHandleID)

参数：
- srcGroupID（输入）：通信域编号，即后续通信任务所等待的通信任务所在的通信域编号。
- srcHandleID（输入）：通信任务，即后续通信任务所等待的通信任务的标识HcclHandle。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 本接口在AIC核或者AIV核上调用必须与对应的Prepare接口的调用核保持一致。
- 一个通信域内，所有Prepare接口和InterHcclGroupSync接口的总调用次数不能超过63。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
