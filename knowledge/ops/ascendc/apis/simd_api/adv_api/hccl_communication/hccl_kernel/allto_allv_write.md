---
type: API
title: AlltoAllvWrite
description: 集合通信AlltoAllvWrite任务下发接口，支持定制发送偏移和数据大小，实现卡间数据的点对点写入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/AlltoAllvWrite.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AlltoAllvWrite

集合通信AlltoAllvWrite的任务下发接口，返回该任务的标识handleId给用户。 AlltoAllvWrite的功能为：通信域内的卡互相发送和接收数据，并且定制每张卡给其它卡发送的数据量和从其它卡接收的数据量，以及定制发送和接收的数据在内存中的偏移。结合原型中的参数，描述接口功能，具体为：本卡发送地址偏移为sendOffsets[i]字节且大小为sendSizes[i]字节的数据给第i张卡，remoteWinOffset表示本卡数据写入对端window的偏移，localDataSize表示各张对端卡写入本卡的数据大小。注意：这里的偏移和数据量均为字节数。

函数原型：
template <bool commit = false>
__aicore__ inline HcclHandle AlltoAllvWrite(GM_ADDR usrIn, GM_ADDR sendOffsets, GM_ADDR sendSizes, uint64_t remoteWinOffset, uint64_t localDataSize)

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。/false：在调用Prepare接口时，不通知服务端执行该通信任务。
- usrIn（输入）：源数据buffer地址。
- sendOffsets（输入）：待发送的每个分片的偏移，以字节为单位。
- sendSizes（输入）：待发送的每个分片的数据大小，以字节为单位。
- remoteWinOffset（输入）：本卡数据写入对端window的偏移，以字节为单位。

返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 若HCCL对象的模板参数config未指定下发通信任务的核，则该接口只能在AIC核或者AIV核两者之一上调用。若HCCL对象的模板参数config指定了下发通信任务的核，则该接口可以在AIC核和AIV核上同时调用，接口内部根据指定的核的类型，在对应的AIC核、AIV核二者之一下发该通信任务。
- 一个通信域内，所有Prepare接口和InterHcclGroupSync接口的总调用次数不能超过63。
- 对于Ascend 950PR/Ascend 950DT，通信服务端为CCU时，默认仅支持FullMesh算法，并且单次最大通信数据量不能超过256M。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AlltoAll](allto_all.md)（`related`）：《AlltoAll》说明集合通信AlltoAll的任务下发接口，返回该任务的标识handleId给用户。AlltoAll的功能为：每张卡向通信域内所有卡发送相同数据量的数据，并从所有卡接收相同数据量的数据。结合原型中的参数，描述接口功能，具体为，第j张卡接收到来自第i张卡的sendBuf中第j块数据，并将该数据存放到本卡recvBuf中第i块的位置。；《AlltoAllvWrite》说明集合通信AlltoAllvWrite任务下发接口，支持定制发送偏移和数据大小，实现卡间数据的点对点写入。。二者在AlltoAll任务下发返回的handle必须进入HCCL的Commit、Query/Wait和Finalize执行链，且通信域rank布局决定收发分块上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《AlltoAllvWrite》说明集合通信AlltoAllvWrite任务下发接口，支持定制发送偏移和数据大小，实现卡间数据的点对点写入。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《AlltoAllvWrite》说明集合通信AlltoAllvWrite任务下发接口，支持定制发送偏移和数据大小，实现卡间数据的点对点写入。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [GetRankDim](get_rank_dim.md)（`related`）：AlltoAllvWrite 与《GetRankDim》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetRankId](get_rank_id.md)（`related`）：AlltoAllvWrite 与《GetRankId》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetWindowsInAddr](get_windows_in_addr.md)（`related`）：AlltoAllvWrite 与《GetWindowsInAddr》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [GetWindowsOutAddr](get_windows_out_addr.md)（`related`）：AlltoAllvWrite 与《GetWindowsOutAddr》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL模板参数](hccl_template_params.md)（`related`）：AlltoAllvWrite 与《HCCL模板参数》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：AlltoAllvWrite 与《SetCcTilingV2》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Commit（HCCL集合通信）](commit.md)（`same_topic`）：AlltoAllvWrite 与《Commit（HCCL集合通信）》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Finalize（HCCL集合通信）](finalize.md)（`same_topic`）：AlltoAllvWrite 与《Finalize（HCCL集合通信）》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：AlltoAllvWrite 与《HCCL Kernel侧接口》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL使用说明](hccl_usage.md)（`same_topic`）：AlltoAllvWrite 与《HCCL使用说明》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：AlltoAllvWrite 与《HCCL集合通信Wait》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [InitV2](init_v2.md)（`same_topic`）：AlltoAllvWrite 与《InitV2》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [Query（HCCL集合通信）](query.md)（`same_topic`）：AlltoAllvWrite 与《Query（HCCL集合通信）》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
<!-- cannbot:related:end -->
