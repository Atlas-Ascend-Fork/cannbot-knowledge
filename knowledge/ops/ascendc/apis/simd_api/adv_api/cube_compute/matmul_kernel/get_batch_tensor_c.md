---
type: API
title: GetBatchTensorC
description: 调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA,
  batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetBatchTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetBatchTensorC

调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。

函数原型：
template <bool sync = true>
__aicore__ inline GlobalTensor<DstT> GetBatchTensorC(uint32_t batchA, uint32_t batchB, bool enSequentialWrite = false)

参数：
- sync：当前仅支持异步模式，即该参数只支持取值为false。
- batchA（输入）：左矩阵的batch数。
- batchB（输入）：右矩阵的batch数。
- enSequentialWrite（输入）：该参数预留，保持默认值false即可。
- c：输入C矩阵放置于Local Memory的地址，用于保存矩阵分片。

返回值：GlobalTensor，返回计算的矩阵分片。

约束：
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。
- C矩阵片输出到Local Memory，且单核计算的N方向大小singleCoreN非32字节对齐的场景，C矩阵的CubeFormat仅支持ND_ALIGN格式，输出C矩阵片时，自动将singleCoreN方向上的数据补齐至32字节。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：GetBatchTensorC 与《Batch Matmul基础功能》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [GetTensorC](get_tensor_c.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《GetBatchTensorC》说明调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA, batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [SetBatchNum](../matmul_tiling/set_batch_num.md)（`related`）：《GetBatchTensorC》明确“调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA, batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。”；它与《SetBatchNum》的“设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetBatchC](get_batch_c.md)（`same_topic`）：GetBatchTensorC 与《GetBatchC》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch 与《GetBatchTensorC》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
- [SetBatchInfoForNormal](../matmul_tiling/set_batch_info_for_normal.md)（`same_topic`）：GetBatchTensorC 与《SetBatchInfoForNormal》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [SetWorkspace](set_workspace.md)（`same_topic`）：GetBatchTensorC 与《SetWorkspace》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [WaitIterateBatch](wait_iterate_batch.md)（`same_topic`）：GetBatchTensorC 与《WaitIterateBatch》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
<!-- cannbot:related:end -->
