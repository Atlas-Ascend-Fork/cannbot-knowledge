---
type: API
title: Iterate
description: 细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Iterate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a3]
---


# Iterate

在某些算法下，一次完整的集合通信任务可以细分为多个步骤，对每个步骤的数据完成点对点的通信任务，称为细粒度通信。以通信算法"AlltoAll=level0:fullmesh;level1:pairwise"、通信步长为1的AlltoAllV通信任务为例，这里参数level0代表配置Server（昇腾AI Server，通常是8卡或16卡的昇腾NPU设备组成的服务器形态的统称）内通信算法，参数level1代表配置Server间通信算法，fullmesh为全连接通信算法，pairwise为逐对通信算法；如下图所示，该示例展示了AlltoAllV通信的所有待发送数据、每一步通信完成后各卡收到的数据。

函数原型：
template <bool sync = true>
__aicore__ inline int32_t Iterate(HcclHandle handleId, uint16_t* seqSlices, uint16_t seqSliceLen)

参数：
- sync（输入）：bool类型。是否需要等待当前通信步骤完成再进行后续计算或通信任务，参数取值如下：true：默认值，表示阻塞并等待当前通信步骤完成。该参数取值为true时，无需再调用Wait接口等待通信任务完成。
- handleId（输入）：对应通信任务的标识ID，只能使用Prepare原语接口的返回值。/using HcclHandle = int8_t;
- seqSlices（输出）：由用户申请的栈空间，用于保存当前通信步骤的输入或输出数据块的索引下标。在先计算后通信场景，该参数返回当前通信步骤需要的输入数据块索引；在先通信后计算场景，该参数返回当前通信步骤的输出数据块索引。
- seqSliceLen（输入）：seqSlices数组的长度。根据算法的通信步长及算法逻辑，取每一步通信需要保存的数据块索引个数为该数组长度。

返回值：- 当通信任务未结束时：

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 入参handleId只能使用Prepare原语对应接口的返回值。
- 本接口当前支持的通信算法为"AlltoAll=level0:fullmesh;level1:pairwise"。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [算子实现](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/operator_impl.md)（`explains`）：算子实现 与《Iterate》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [Commit（HCCL集合通信）](commit.md)（`related`）：“Iterate”定义：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。；“Commit（HCCL集合通信）”定义：非细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的步长长度的子通信任务。。实质衔接：细粒度 Iterate 取得每一步输入/输出后，Commit 推进一步通信，Query/Wait 观测或阻塞对应轮次，构成计算通信流水的可执行闭环。
- [HCCL使用说明](hccl_usage.md)（`related`）：“Iterate”定义：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。；“HCCL使用说明”定义：Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。实质衔接：细粒度 Iterate 取得每一步输入/输出后，Commit 推进一步通信，Query/Wait 观测或阻塞对应轮次，构成计算通信流水的可执行闭环。
- [Query（HCCL集合通信）](query.md)（`related`）：“Iterate”定义：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。；“Query（HCCL集合通信）”定义：查询handleId对应的通信任务已经完成的轮次，最多返回repeat轮。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。实质衔接：细粒度 Iterate 取得每一步输入/输出后，Commit 推进一步通信，Query/Wait 观测或阻塞对应轮次，构成计算通信流水的可执行闭环。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Iterate正文界定“细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL集合通信Wait](wait.md)（`same_topic`）：HCCL集合通信Wait：Wait消费 Prepare原语返回的 handle，必须在InitV2/SetCcTilingV2后按Commit与Prepare顺序阻塞；Query提供非阻塞完成检查，Iterate定义细粒度步数。 目标卡《Iterate》补充：细粒度通信接口，获取集合通信算法每一步的输入或输出，实现计算与通信的精细粒度流水排布。
- [SetStepSize](../hccl_tiling/set_step_size.md)（`same_topic`）：SetStepSize 与《Iterate》的实质衔接是：SetStepSize 把细粒度通信一次推进的算法步数写入 HcclTilingData，并与算法、通信块、引擎、队列配置一起驱动 Iterate/Commit/Wait 的 AlltoAllV 流程。
<!-- cannbot:related:end -->
