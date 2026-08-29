---
type: API
title: HCCL集合通信Wait
description: 阻塞AI Core，非细粒度通信时，等待handleId对应的通信任务完成，细粒度通信时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# HCCL集合通信Wait

阻塞AI Core，非[细粒度通信](iterate.md)时，等待handleId对应的通信任务完成，[细粒度通信](iterate.md)时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。

函数原型：__aicore__ inline int32_t Wait(HcclHandle handleId)

参数：
- handleId（输入）：对应通信任务的标识ID，只能使用Prepare原语接口的返回值。/using HcclHandle = int8_t;

返回值：- 0，表示成功

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 入参handleId只能使用Prepare原语对应接口的返回值。
- 本接口在AIC核或者AIV核上调用必须与对应的Prepare接口的调用核保持一致。
- 非细粒度通信时，本接口的调用次数应该与Prepare的repeat次数一致，细粒度通信时，本接口的调用次数应该与通信任务的总步骤数 步长*Prepare的repeat次数一致。handleId调用Wait接口的顺序，必须和Prepare接口一致。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AllGather](all_gather.md)（`related`）：返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。；阻塞AI Core，非［细粒度通信］(iterate.md)时，等待handleId对应的通信任务完成，［细粒度通信］(iterate.md)时，等待handleId对应的步长长度的子通信任务完成。。AllGather 产出的有效 handleId 被 Wait 用于等待相同通信任务完成，联合阅读可闭合下发到完成同步。
- [Iterate](iterate.md)（`related`）：阻塞AI Core，非［细粒度通信］(iterate.md)时，等待handleId对应的通信任务完成，［细粒度通信］(iterate.md)时，等待handleId对应的步长长度的子通信任务完成。；sync（输入）：bool类型。是否需要等待当前通信步骤完成再进行后续计算或通信任务，参数取值如下：true：默认值，表示阻塞并等待当前通信步骤完成。该参数取值为true时，无需再调用Wait接口等待通信任务完成。两接口通过 Iterate 的 sync 选择共同决定每个细粒度步骤是否另行 Wait。
- [Query（HCCL集合通信）](query.md)（`related`）：Query 用于“查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。”；Wait 用于“等待handleId对应的通信任务完成”。二者分别支持非阻塞进度观测和阻塞完成，是同一 handle 生命周期的两种同步策略。
<!-- cannbot:related:end -->
