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

- [IterateNBatch](iterate_n_batch.md)（`related`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。；IterateNBatch 异步生产多 Batch 结果，GetBatchC 的同功能替代接口负责逐片消费。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；两端定义同一 C 分片获取合同，焦点还给出向 GetBatchTensorC 的明确迁移建议。
<!-- cannbot:related:end -->
