---
type: API
title: ReduceScatter
description: 集合通信算子ReduceScatter的任务下发接口，返回该任务的标识handleId给用户。ReduceScatter的功能为：将所有rank的输入相加（或其他归约操作）后，再把结果按照rank编号均匀分散到各个rank的输出buffer，每个进程拿到其他进程1/ranksize份的数据进行归约操作。
  !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/ReduceScatter.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ReduceScatter

集合通信算子ReduceScatter的任务下发接口，返回该任务的标识handleId给用户。ReduceScatter的功能为：将所有rank的输入相加（或其他归约操作）后，再把结果按照rank编号均匀分散到各个rank的输出buffer，每个进程拿到其他进程1/ranksize份的数据进行归约操作。

函数原型：
template <bool commit = false>
__aicore__ inline HcclHandle ReduceScatter(GM_ADDR sendBuf, GM_ADDR recvBuf, uint64_t recvCount, HcclDataType dataType, HcclReduceOp op, uint64_t strideCount, uint8_t repeat = 1)

参数：
- commit（输入）：bool类型。参数取值如下：true：在调用Prepare接口时，Commit同步通知服务端可以执行该通信任务。/false：在调用Prepare接口时，不通知服务端执行该通信任务。
- sendBuf（输入）：源数据buffer地址。
- recvBuf（输出）：目的数据buffer地址，集合通信结果输出到此buffer中。
- recvCount（输入）：参与ReduceScatter操作的recvBuf的数据个数；sendBuf的数据个数等于recvCount * rank size。
- dataType（输入）：ReduceScatter操作的数据类型，目前支持float、half、int8_t、int16_t、int32_t、bfloat16_t数据类型，即支持取值为HCCL_DATA_TYPE_FP32、HCCL_DATA_TYPE_FP16、HCCL_DATA_TYPE_INT8、HCCL_DATA_TYPE_INT16、HCCL_DATA_TYPE_INT32、HCCL_DATA_TYPE_BFP16。

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

- [UDMA GET size=0 污染后续 GET 致精度失败](../../../../../runbooks/precision/udma_get_size_zero_pollutes_engine_guard.md)（`exemplifies`）：在 matmul_reducescatter（MC2 通算融合，4P SHMEM ReduceScatter，Pattern B）实现通算流水后跑精度回归：M=2048 N=3584 K=5120、4 卡、tileCnt=2。 ReduceScatter的功能为：将所有rank的输入相加（或其他归约操作）后，再把结果按照rank编号均匀分散到各个rank的输出buffer，每个进程拿到其他进程1/ranksize份的数据进行归约操作。 按 tile/rank 实现 ReduceScatter 时会合法出现 hasOverlap=false，Runbook 要求 UDMA GET 前显式守卫零字节。
- [逐 rank 通信路径的 MTE2 主导诊断](../../../../../runbooks/performance/rank_flag_mte2.md)（`exemplifies`）：matmul_reducescatter（MC2 通算融合，4P SHMEM ReduceScatter）的 AIV 侧 `ReduceSegmentParallel` 对每个远程 rank 逐次 `DataCopy`，前后带 `V_MTE2/MTE2_V` 同步。 ReduceScatter的功能为：将所有rank的输入相加（或其他归约操作）后，再把结果按照rank编号均匀分散到各个rank的输出buffer，每个进程拿到其他进程1/ranksize份的数据进行归约操作。 逐 rank 拉取和归约是在实现 ReduceScatter 的跨 rank 汇聚/分散，msprof MTE2 指标定位该数据阶段的主导耗时。
- [InitV2](init_v2.md)（`related`）：调用本接口前确保已调用过InitV2和SetCcTilingV2接口。；HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。ReduceScatter 的强制前置步骤由 InitV2 卡补充 context、initTiling 和工作核约束。
- [MatmulReduceScatter 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_reduce_scatter_950.md)（`related`）：各 rank 的完整结果按 `sum` 归约后沿 M 轴等分，本 rank 输出 `y:［M/rankSize,N］`。；ReduceScatter的功能为：将所有rank的输入相加（或其他归约操作）后，再把结果按照rank编号均匀分散到各个rank的输出buffer；前者的通信阶段正是后者定义的求和并按 rank 分散合同。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：调用本接口前确保已调用过InitV2和SetCcTilingV2接口。；用于设置HCCL客户端中某个通信算法配置的TilingData地址。ReduceScatter 明确要求前置调用，而 SetCcTilingV2 卡给出该前置步骤设置通信算法 TilingData 的参数和覆盖规则。
<!-- cannbot:related:end -->
