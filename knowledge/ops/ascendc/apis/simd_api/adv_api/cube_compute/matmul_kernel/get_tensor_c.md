---
type: API
title: GetTensorC
description: Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetTensorC

Iterate后，获取一块或者两块C矩阵片，可以直接输出到GM tensor中，也可以输出到UB（VECIN）tensor中。当MatmulConfig参数中的ScheduleType取值为ScheduleType::INNER_PRODUCT时，获取一块C矩阵片；当MatmulConfig参数中的ScheduleType取值为ScheduleType::OUTER_PRODUCT时，获取两块C矩阵片。

函数原型：template <bool sync = true>

参数：
- sync：设置同步或者异步模式：同步模式设置为true；异步模式设置为false。
- c/co2Local（输出）：取出C矩阵到UB（VECIN）。不同型号支持的数据类型请参考支持的数据类型。不同型号支持的数据格式请参考支持的数据格式。
- gm（输出）：取出C矩阵到GM，数据格式可以为ND或NZ。不同型号支持的数据类型请参考支持的数据类型。

约束：
- 传入的C矩阵地址空间大小需要保证不小于baseM * baseN。
- 异步场景时，需要使用一块临时空间来缓存Iterate计算结果，调用GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过SetWorkspace接口进行设置。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [单次矩阵乘局部输出](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/single_matmul_local_output.md)（`explains`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《单次矩阵乘局部输出》说明开启Partial Output后Iterate不进行K轴累加，仅输出单次基本块计算结果，由用户自行累加。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [异步场景处理](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`explains`）：异步 Iterate 计算后由 GetTensorC 从 workspace/L0C 取得 C 分片，调用时点决定何时发生同步等待。
- [GetBatchTensorC](get_batch_tensor_c.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《GetBatchTensorC》说明调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA, batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [IterateAll](iterate_all.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [SetWorkspace](set_workspace.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《SetWorkspace》说明Iterate计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。 IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [WaitGetTensorC](wait_get_tensor_c.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《WaitGetTensorC》说明当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [AsyncGetTensorC](async_get_tensor_c.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《AsyncGetTensorC》说明获取Iterate接口异步计算的结果矩阵。该接口功能已被GetTensorC覆盖，建议直接使用GetTensorC异步接口。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [GetOffsetC](get_offset_c.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《GetOffsetC》说明预留接口，为后续功能做预留。 获取本次计算时当前分片在整个C矩阵中的位置。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Iterate](iterate.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《Iterate》说明每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“GetTensorC”明确Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《Matmul使用说明》说明Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
<!-- cannbot:related:end -->
