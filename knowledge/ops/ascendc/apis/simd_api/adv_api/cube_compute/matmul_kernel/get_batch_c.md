---
type: API
title: GetBatchC
description: GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA,
  batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetBatchC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetBatchC

GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。

函数原型：
template <bool sync = true>
__aicore__ inline GlobalTensor<DstT> GetBatchC(uint32_t batchA, uint32_t batchB, bool enSequentialWrite = false)

参数：
- sync：通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。
- batchA（输入）：左矩阵的batch数。
- batchB（输入）：右矩阵的batch数。
- enSequentialWrite（输入）：输出是否连续存放数据，默认false（非连续写模式）。
- c：输入C矩阵，用于保存矩阵分片。类型为LocalTensor。

返回值：GlobalTensor，返回计算的矩阵分片。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：Batch Matmul基础功能 与《GetBatchC》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [AsyncGetTensorC](async_get_tensor_c.md)（`related`）：GetBatchC 与《AsyncGetTensorC》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [SetBatchNum](../matmul_tiling/set_batch_num.md)（`related`）：《GetBatchC》明确“GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA, batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。”；它与《SetBatchNum》的“设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。”在实际调用参数、数据流或结果校验上直接衔接。
- [WaitIterateBatch](wait_iterate_batch.md)（`related`）：GetBatchC 与《WaitIterateBatch》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC 与《GetBatchC》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [IterateBatch](iterate_batch.md)（`same_topic`）：GetBatchC 与《IterateBatch》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch 与《GetBatchC》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
- [SetBatchNum](set_batch_num.md)（`same_topic`）：GetBatchC 与《SetBatchNum》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
<!-- cannbot:related:end -->
