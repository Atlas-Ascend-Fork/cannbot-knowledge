---
type: API
title: AlltoAllV
description: 集合通信AlltoAllV任务下发接口，支持通信域内各卡定制收发数据量和内存偏移，返回任务标识handleId。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/AlltoAllV.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a3]
---


# AlltoAllV

集合通信AlltoAllV的任务下发接口，返回该任务的标识handleId给用户。AlltoAll是AlltoAllV的一个子集，AlltoAll要求所有卡的收发数据量相同，AlltoAllV则不需要数据量相同，使用上更加灵活。 AlltoAllV的功能为：通信域内的卡互相发送和接收数据，并且定制每张卡给其它卡发送的数据量和从其它卡接收的数据量，以及定制发送和接收的数据在内存中的偏移。结合原型中的参数，描述接口功能，具体为：第i张卡发送sendBuf内存中第j块数据到第j张卡，该块数据在sendBuf中偏移为sdispls\[j\]的位置，且数据量为sendCounts\[j\]，第j张卡将该数据存放到本卡recvBuf中偏移为rdispls\[i\]的位置，接收数据量为recvCounts\[i\]，这里的sendCounts\[j\]与recvCounts\[i\]需要相等。

函数原型：template <bool commit = false>

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。。
- sendBuf（输入）：源数据buffer地址。
- sendCounts（输入）：本卡向通信域内其它每张卡发送的数据量，sendCounts[i]表示本卡发送到第i张卡rank_i的数据量，单位是sizeof(sendType)。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 若HCCL对象的config模板参数未指定下发通信任务的核，该接口只能在AIC核或者AIV核两者之一上调用。若HCCL对象的config模板参数中指定了下发通信任务的核，则该接口可以在AIC核和AIV核上同时调用，接口内部会根据指定的核的类型，只在AIC核、AIV核二者之一下发该通信任务。
- 一个通信域内，所有Prepare接口和InterHcclGroupSync接口的总调用次数不能超过63。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [AlltoAll](allto_all.md)（`related`）：焦点卡写明“每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据”，候选卡写明“AlltoAll要求所有卡的收发数据量相同，AlltoAllV则不需要数据量相同”。两卡给出等量与逐 rank 变长收发契约，可决定是否传 counts/displacements。
- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：焦点算子说明“MIX AIV 侧再以 `Hccl<HCCL_SERVER_TYPE_AICPU>` 提交 AllToAllV/AllGather command”，候选 API 定义“定制每张卡给其它卡发送的数据量和从其它卡接收的数据量，以及定制发送和接收的数据在内存中的偏移。”；该合同对应算子 EP 域分片通信的计数与位移参数。
<!-- cannbot:related:end -->
