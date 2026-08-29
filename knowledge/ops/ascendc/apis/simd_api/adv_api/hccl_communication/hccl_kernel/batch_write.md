---
type: API
title: BatchWrite
description: 集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/BatchWrite.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# BatchWrite

集合通信BatchWrite的任务下发接口，返回该任务的标识handleId给用户。BatchWrite实现了一种点对点通信，这是一种直接传输数据的通信模式，能够同时将多份数据发送到不同的Global Memory地址上。 对于Atlas A3 训练系列产品/Atlas A3 推理系列产品，BatchWrite通信支持在相同或不同的昇腾AI Server之间进行。 对于Atlas A2 训练系列产品/Atlas A2 推理系列产品，BatchWrite通信必须在不同昇腾AI Server（通常是8卡或16卡的昇腾NPU设备组成的服务器形态的统称）之间进行。

函数原型：
template <bool commit = false>
__aicore__ inline HcclHandle BatchWrite(GM_ADDR batchWriteInfo, uint32_t itemNum, uint16_t queueID = 0U)

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。/false：在调用Prepare接口时，不通知服务端执行该通信任务。
- batchWriteInfo（输入）：通信任务信息的Global Memory地址。一组通信数据的相关信息必须按指定的格式保存，在执行通信任务时，可以同时指定多组通信任务信息，执行通信任务时批量发送数据。结构体定义如下代码所示。
- itemNum（输入）：批量任务的个数。该参数取值必须与batchWriteInfo中通信任务信息的组数一致。
- queueID（输入）：指定当前通信所在的队列ID，默认值为0。

返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 若HCCL对象的config模板参数未指定下发通信任务的核，该接口只能在AIC核或者AIV核两者之一上调用。若HCCL对象的config模板参数中指定了下发通信任务的核，则该接口可以在AIC核和AIV核上同时调用，接口内部会根据指定的核的类型，只在AIC核、AIV核二者之一下发该通信任务。
- 一个通信域内，所有Prepare接口和InterHcclGroupSync接口的总调用次数不能超过63。
- 对于Atlas A2 训练系列产品/Atlas A2 推理系列产品，当前接口仅支持不同AI Server间的通信，同时通信任务信息中指定的目的卡号不能是本卡号。
- 通信任务信息写入batchWriteInfo前，必须通过调用DataCacheCleanAndInvalid接口，保证预期的数据成功刷新到Global Memory上。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Commit（HCCL集合通信）](commit.md)（`related`）：集合通信BatchWrite的任务下发接口，返回该任务的标识handleId给用户。；非［细粒度通信］(iterate.md)时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。。BatchWrite 产生通信任务 handle，Commit 以该 handle 通知服务端执行，二者构成 Prepare/提交的连续任务生命周期。
- [GetQueueNum](get_queue_num.md)（`related`）：焦点卡“获取BatchWrite通信任务的通信队列数量。”，候选卡要求“queueID（输入）：指定当前通信所在的队列ID，默认值为0。”；查询队列总数为 BatchWrite 选择合法 queueID 提供运行时边界。
- [QueueBarrier](queue_barrier.md)（`related`）：BatchWrite实现了一种点对点通信，这是一种直接传输数据的通信模式，能够同时将多份数据发送到不同的Global Memory地址上。；阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。。BatchWrite 在队列中下发多目的地址通信，QueueBarrier 则等待这些 BatchWrite 队列任务完成，是同一执行链的同步收口。
- [SetCommBlockNum](../hccl_tiling/set_comm_block_num.md)（`related`）：设置参与BatchWrite通信的核数。；集合通信BatchWrite的任务下发接口，返回该任务的标识handleId给用户。；Tiling 接口生产 BatchWrite 的参与核数，Kernel 接口消费该配置下发点对点批量通信任务，形成参数生产到任务执行的直接合同。
- [SetQueueNum](../hccl_tiling/set_queue_num.md)（`related`）：设置每个向服务端下发任务的核上的BatchWrite通信队列数量；queueID（输入）：指定当前通信所在的队列ID，默认值为0；配置页决定 BatchWrite 调用中 queueID 的可用队列域。
<!-- cannbot:related:end -->
