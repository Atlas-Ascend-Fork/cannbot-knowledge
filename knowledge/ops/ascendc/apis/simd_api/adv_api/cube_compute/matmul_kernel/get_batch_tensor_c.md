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

- [GetBatchC](get_batch_c.md)（`same_topic`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；两端定义同一 C 分片获取合同，焦点还给出向 GetBatchTensorC 的明确迁移建议。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：该接口可以与IterateNBatch异步接口配合使用；调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。GetBatchTensorC 定义异步结果分片的获取，IterateNBatch 明确在 waitIterateBatch=false 路径调用该接口，形成生产与取回 C 矩阵的直接调用合同。
<!-- cannbot:related:end -->
