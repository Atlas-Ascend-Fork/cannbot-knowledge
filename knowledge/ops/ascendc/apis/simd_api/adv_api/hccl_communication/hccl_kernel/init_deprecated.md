---
type: API
title: Init（废弃）
description: HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Init_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Init（废弃）

HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline void Init(GM_ADDR context, __gm__ void* initTiling = nullptr)

参数：
- context（输入）：通信上下文，包含rankDim，rankID等相关信息。
- initTiling（输入）：可选参数，通信域初始化Mc2InitTiling的地址。Mc2InitTiling在Host侧计算得出，具体请参考表1 Mc2InitTiling参数说明，由框架传递到Kernel函数中使用，完整示例请参考8.13.1.2-调用示例。

约束：
- 若调用本接口时传入initTiling参数，则必须与SetCcTiling接口配合使用。
- 同一个程序中不能同时调用传入可选参数initTiling的接口和不传入可选参数initTiling的接口，推荐使用传入initTiling参数的调用方式。
- 若调用本接口时传入initTiling参数，必须使用标准C++语法定义TilingData结构体的开发方式。
- 本接口不支持使用相同的context初始化多个HCCL对象。每个HCCL对象都应获取其自身的通信上下文。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [SetCcTiling（废弃）](set_cc_tiling_deprecated.md)（`related`）：若调用本接口时传入initTiling参数，则必须与SetCcTiling接口配合使用。；若调用本接口，必须与传initTiling地址的Init接口配合使用，且Init接口在本接口前被调用。。Init 与 SetCcTiling 双方正文互相规定配套调用及先后顺序，组成同一 deprecated 初始化合同。
- [InitV2](init_v2.md)（`same_topic`）：函数原型：__aicore__ inline void InitV2(GM_ADDR context, const void* initTiling)；函数原型：__aicore__ inline void Init(GM_ADDR context, __gm__ void* initTiling = nullptr)。两卡描述同一 HCCL 客户端初始化契约的新旧入口；V2 强制 initTiling 与 SetCcTilingV2，而旧入口保留可选参数和旧配套接口。
<!-- cannbot:related:end -->
