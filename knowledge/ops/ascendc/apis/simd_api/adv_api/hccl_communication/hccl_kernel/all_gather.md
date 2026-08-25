---
type: API
title: AllGather
description: 集合通信算子AllGather的任务下发接口，返回该任务的标识handleId给用户。AllGather的功能为：将通信域内所有节点的输入按照rank
  id重新排序，然后拼接起来，再将结果发送到所有节点的输出。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/AllGather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# AllGather

集合通信算子AllGather的任务下发接口，返回该任务的标识handleId给用户。AllGather的功能为：将通信域内所有节点的输入按照rank id重新排序，然后拼接起来，再将结果发送到所有节点的输出。

函数原型：
template <bool commit = false>
__aicore__ inline HcclHandle AllGather(GM_ADDR sendBuf, GM_ADDR recvBuf, uint64_t sendCount, HcclDataType dataType, uint64_t strideCount, uint8_t repeat = 1)

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。/false：在调用Prepare接口时，不通知服务端执行该通信任务。
- sendBuf（输入）：源数据buffer地址。
- recvBuf（输出）：目的数据buffer地址，集合通信结果输出到此buffer中。
- sendCount（输入）：参与AllGather操作的sendBuf的数据个数；recvBuf的数据个数等于sendCount * rank size，即sendCount * 卡数。
- dataType（输入）：AllGather操作的数据类型，目前支持HcclDataType包含的全部数据类型，HcclDataType详细可参考表1。

返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 若HCCL对象的config模板参数未指定下发通信任务的核，该接口只能在AIC核或者AIV核两者之一上调用。若HCCL对象的config模板参数中指定了下发通信任务的核，则该接口可以在AIC核和AIV核上同时调用，接口内部会根据指定的核的类型，只在AIC核、AIV核二者之一下发该通信任务。
- 对于Atlas A2 训练系列产品/Atlas A2 推理系列产品，一个通信域内，所有Prepare接口的总调用次数不能超过63。
- 对于Atlas A3 训练系列产品/Atlas A3 推理系列产品，一个通信域内，所有Prepare接口和InterHcclGroupSync接口的总调用次数不能超过63。
- 对于Ascend 950PR/Ascend 950DT，一个通信域内，所有Prepare接口的总调用次数不能超过63。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Commit（HCCL集合通信）](commit.md)（`related`）：commit=false 的 AllGather 只准备并返回 handle，随后需 Commit 通知服务端执行该 handle 对应任务。
- [GetRankDim](get_rank_dim.md)（`related`）：AllGather 的输入拼接和输出布局按通信域内 rank 数及 rank id 排列，RankDim 是分配结果空间的依据。
- [HCCL集合通信Wait](wait.md)（`related`）：Wait 按 Prepare 顺序等待 AllGather 返回 handle 的任务完成，闭合异步下发到消费结果的同步协议。
- [InitV2](init_v2.md)（`related`）：AllGather 下发前明确要求完成 InitV2，后者建立 HCCL 客户端状态，是任务创建的前置步骤。
- [ReduceScatter](reduce_scatter.md)（`related`）：ReduceScatter：ReduceScatter 的通信语义可分解为归约后分散，其 handle 必须进入 HCCL 的 Init/Commit/Query/Wait 生命周期；AllReduce/AllGather用于精确区分其数据分布语义。 目标卡《AllGather》补充：集合通信算子AllGather的任务下发接口，返回该任务的标识handleId给用户。AllGather的功能为：将通信域内所有节点的输入按照rank id重新排序，然后拼接起来，再将结果发送到所有节点的输出。 !
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：AllGather 约束要求先设置通信算法 TilingData 地址，SetCcTilingV2 正是该前置配置接口。
- [HCCL使用说明](hccl_usage.md)（`same_topic`）：使用说明串联 Init、SetCcTiling、AllGather、Commit 与 Wait，可据 commit 模板参数选择完整执行序列。
<!-- cannbot:related:end -->
