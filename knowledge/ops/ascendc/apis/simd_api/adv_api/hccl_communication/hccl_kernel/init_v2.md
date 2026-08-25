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

<!-- cannbot:related:start -->
## 相关

- [AllGather](all_gather.md)（`related`）：AllGather 下发前明确要求完成 InitV2，后者建立 HCCL 客户端状态，是任务创建的前置步骤。
- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《InitV2》说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《InitV2》说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [Finalize（HCCL集合通信）](finalize.md)（`related`）：Finalize（HCCL集合通信） 与《InitV2》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [GET_TILING_DATA_WITH_STRUCT](../../../basic_api/kernel_tiling/get_tiling_data_with_struct.md)（`related`）：InitV2 的 initTiling 不能是 GM 地址，推荐由该宏取得 TilingData 栈地址后传入。
- [GetHcclContext](../hccl_context/get_hccl_context.md)（`related`）：InitV2 的 context 参数来自 GetHcclContext，包含 rankDim/rankID 等通信上下文。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《InitV2》说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [GetRankDim](get_rank_dim.md)（`related`）：RankDim 来源于 InitV2 建立的 HCCL 客户端通信域，应在初始化完成后读取。
- [HcclTilingData](../hccl_tiling/tiling_data_struct.md)（`related`）：InitV2 消费 HcclTilingData 起始处的 Mc2InitTiling 栈地址来初始化客户端，并要求标准 C++ 结构定义；这与 focal 给出的结构布局直接衔接。
- [Query（HCCL集合通信）](query.md)（`related`）：Query 前必须 InitV2 建立 HCCL 客户端和通信上下文。
- [ReduceScatter](reduce_scatter.md)（`related`）：ReduceScatter：ReduceScatter 的通信语义可分解为归约后分散，其 handle 必须进入 HCCL 的 Init/Commit/Query/Wait 生命周期；AllReduce/AllGather用于精确区分其数据分布语义。 目标卡《InitV2》补充：HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [AllReduce](all_reduce.md)（`same_topic`）：AllReduce 与《InitV2》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [AlltoAllvWrite](allto_allv_write.md)（`same_topic`）：AlltoAllvWrite 与《InitV2》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；InitV2正文界定“HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL Tiling侧接口](../hccl_tiling/hccl_tiling.md)（`same_topic`）：InitV2说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [HCCL模板参数](hccl_template_params.md)（`same_topic`）：InitV2 在实例化 HCCL 对象后完成初始化，模板选定的服务端和下发核由此进入实际通信生命周期。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：HCCL集合通信Wait：Wait消费 Prepare原语返回的 handle，必须在InitV2/SetCcTilingV2后按Commit与Prepare顺序阻塞；Query提供非阻塞完成检查，Iterate定义细粒度步数。 目标卡《InitV2》补充：HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [Init（废弃）](init_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；InitV2正文说明“HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`same_topic`）：InitV2说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [SetHcclContext](../hccl_context/set_hccl_context.md)（`same_topic`）：SetHcclContext 与《InitV2》的实质衔接是：SetHcclContext 把指定通信域消息区地址绑定给 HCCL 对象；GetHcclContext、Context/Kernel 使用说明与 InitV2 构成配置和消费两端。
<!-- cannbot:related:end -->
