---
type: API
title: InitV2
description: HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/InitV2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# InitV2

HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline void InitV2(GM_ADDR context, const void* initTiling)

参数：
- context（输入）：通信上下文，包含rankDim，rankID等相关信息。通过框架提供的获取通信上下文的接口GetHcclContext获取context。
- initTiling（输入）：通信域初始化Mc2InitTiling的地址。Mc2InitTiling在Host侧计算得出，具体请参考表1 Mc2InitTiling参数说明，由框架传递到Kernel函数中使用。

约束：
- 本接口必须与SetCcTilingV2接口配合使用。
- 调用本接口时，必须使用标准C++语法定义TilingData结构体的开发方式。
- 调用本接口传入的initTiling参数，不能使用Global Memory地址，建议通过GET_TILING_DATA_WITH_STRUCT接口获取TilingData的栈地址。
- 本接口不支持使用相同的context初始化多个HCCL对象。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。
