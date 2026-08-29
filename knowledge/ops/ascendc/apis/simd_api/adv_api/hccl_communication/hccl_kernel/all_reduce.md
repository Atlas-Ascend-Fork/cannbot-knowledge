---
type: API
title: AllReduce
description: 集合通信算子AllReduce的任务下发接口，返回该任务的标识handleId给用户。AllReduce功能为：将通信域内所有节点的同名张量进行reduce操作后，再把结果发送到所有节点的输出buffer。
  !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/AllReduce.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# AllReduce

集合通信算子AllReduce的任务下发接口，返回该任务的标识handleId给用户。AllReduce功能为：将通信域内所有节点的同名张量进行reduce操作后，再把结果发送到所有节点的输出buffer。

函数原型：
template <bool commit = false>
__aicore__ inline HcclHandle AllReduce(GM_ADDR sendBuf, GM_ADDR recvBuf, uint64_t count, HcclDataType dataType, HcclReduceOp op, uint8_t repeat = 1)

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。/false：在调用Prepare接口时，不通知服务端执行该通信任务。
- sendBuf（输入）：源数据buffer地址。
- recvBuf（输出）：目的数据buffer地址，集合通信结果输出到此buffer中。
- count（输入）：参与AllReduce操作的数据个数，比如只有一个int32数据参与，则count=1。
- dataType（输入）：AllReduce操作的数据类型，目前支持float、half（即float16）、int8_t、int16_t、int32_t、bfloat16_t数据类型，即支持取值为HCCL_DATA_TYPE_FP32、HCCL_DATA_TYPE_FP16、HCCL_DATA_TYPE_INT8、HCCL_DATA_TYPE_INT16、HCCL_DATA_TYPE_INT32、HCCL_DATA_TYPE_BFP16。

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

- [MatmulAllReduce 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_950.md)（`related`）：算子路线说明“其它 rank 直接 `AllReduce(C1)`。”；接口卡规定“调用本接口前确保已调用过InitV2和SetCcTilingV2接口。”，将普通 rank 的通信节点落到 AllReduce 的前置初始化与 tiling 配置合同。
- [MatmulAllReduceAddRmsNorm A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_all_reduce_add_rms_norm.md)（`related`）：融合算子语义为“`mmOut=AllReduce(x1@x2+bias,SUM)`”；HCCL 接口说明“将通信域内所有节点的同名张量进行reduce操作后，再把结果发送到所有节点的输出buffer。”，把融合节点中的 SUM 归约落到具体 send/recv buffer、count 和前置 tiling 合同。
<!-- cannbot:related:end -->
