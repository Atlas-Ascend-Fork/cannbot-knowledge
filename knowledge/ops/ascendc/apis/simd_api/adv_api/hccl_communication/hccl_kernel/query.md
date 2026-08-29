---
type: API
title: Query（HCCL集合通信）
description: 查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Query.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# Query（HCCL集合通信）

查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline int32_t Query(HcclHandle handleId)

参数：
- handleId（输入）：对应通信任务的标识ID，只能使用Prepare原语接口的返回值。/using HcclHandle = int8_t;

返回值：- 返回handleId对应的通信任务已执行的次数，最大值为repeat。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 入参handleId只能使用Prepare原语对应接口的返回值。
- 本接口在AIC核或者AIV核上调用必须与对应的Prepare接口的调用核保持一致。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [HCCL集合通信Wait](wait.md)（`related`）：Query 用于“查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。”；Wait 用于“等待handleId对应的通信任务完成”。二者分别支持非阻塞进度观测和阻塞完成，是同一 handle 生命周期的两种同步策略。
<!-- cannbot:related:end -->
