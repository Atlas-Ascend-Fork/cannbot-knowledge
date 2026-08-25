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

- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《AlltoAllV》说明集合通信AlltoAllV任务下发接口，支持通信域内各卡定制收发数据量和内存偏移，返回任务标识handleId。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [Commit（HCCL集合通信）](commit.md)（`related`）：commit=false 的 AlltoAllV 只 Prepare 并返回 handle，需 Commit 通知服务端实际执行。
- [HCCL集合通信Wait](wait.md)（`related`）：Wait 按 Prepare 顺序等待 AlltoAllV handle 完成，避免在变长收发结果就绪前消费 recvBuf。
- [SetStepSize](../hccl_tiling/set_step_size.md)（`same_topic`）：SetStepSize 与《AlltoAllV》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
