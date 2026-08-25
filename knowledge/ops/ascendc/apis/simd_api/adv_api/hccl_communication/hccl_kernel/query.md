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

- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《Query（HCCL集合通信）》说明查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《Query（HCCL集合通信）》说明查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [Commit（HCCL集合通信）](commit.md)（`related`）：Query 可在 Commit 后检查同一通信任务的完成状态，为不阻塞的进度判断提供接口。
- [InitV2](init_v2.md)（`related`）：Query 前必须 InitV2 建立 HCCL 客户端和通信上下文。
- [Iterate](iterate.md)（`related`）：“Iterate”定义：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。；“Query（HCCL集合通信）”定义：查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。实质衔接：细粒度 Iterate 取得每一步输入/输出后，Commit 推进一步通信，Query/Wait 观测或阻塞对应轮次，构成计算通信流水的可执行闭环。
- [ReduceScatter](reduce_scatter.md)（`related`）：ReduceScatter：ReduceScatter 的通信语义可分解为归约后分散，其 handle 必须进入 HCCL 的 Init/Commit/Query/Wait 生命周期；AllReduce/AllGather用于精确区分其数据分布语义。 目标卡《Query（HCCL集合通信）》补充：查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：Query 明确依赖 SetCcTilingV2 配置通信任务的 repeat 等 tiling。
- [AllReduce](all_reduce.md)（`same_topic`）：AllReduce 与《Query（HCCL集合通信）》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [AlltoAllvWrite](allto_allv_write.md)（`same_topic`）：AlltoAllvWrite 与《Query（HCCL集合通信）》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Query（HCCL集合通信）正文界定“查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：HCCL集合通信Wait：Wait消费 Prepare原语返回的 handle，必须在InitV2/SetCcTilingV2后按Commit与Prepare顺序阻塞；Query提供非阻塞完成检查，Iterate定义细粒度步数。 目标卡《Query（HCCL集合通信）》补充：查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。
<!-- cannbot:related:end -->
