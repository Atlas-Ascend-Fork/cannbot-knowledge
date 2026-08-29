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

- [AllGatherMatmul 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/all_gather_matmul_950.md)（`related`）：焦点卡的 Device 流程是“所有 tile 先异步提交，AIC 同时计算本地块；远端块只等待对应 handle”，候选 API 返回“该任务的标识handleId”；算子正是用 AllGather 的 handle 粒度等待来解锁各远端 Matmul tile。
- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：焦点算子说明“MIX AIV 侧再以 `Hccl<HCCL_SERVER_TYPE_AICPU>` 提交 AllToAllV/AllGather command”，候选 API 规定“recvBuf的数据个数等于sendCount * rank size，即sendCount * 卡数。”；该接口合同直接解释算子 TP 域 AllGather 的输出扩张和 buffer 规划。
- [Commit（HCCL集合通信）](commit.md)（`related`）：集合通信算子AllGather的任务下发接口，返回该任务的标识handleId给用户。；非［细粒度通信］(iterate.md)时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。。AllGather 返回的 handleId 正是 Commit 通知服务端执行该已准备通信任务所消费的标识，二者形成准备后提交的调用链。
- [HCCL集合通信Wait](wait.md)（`related`）：返回值：返回该任务的标识handleId，handleId大于等于0。调用失败时，返回 -1。；阻塞AI Core，非［细粒度通信］(iterate.md)时，等待handleId对应的通信任务完成，［细粒度通信］(iterate.md)时，等待handleId对应的步长长度的子通信任务完成。。AllGather 产出的有效 handleId 被 Wait 用于等待相同通信任务完成，联合阅读可闭合下发到完成同步。
<!-- cannbot:related:end -->
