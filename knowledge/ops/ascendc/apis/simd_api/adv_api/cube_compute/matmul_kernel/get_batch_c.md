---
type: API
title: GetBatchC
description: GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA,
  batchB\) \ singleCoreM \ singleCoreN大小的矩阵分片。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetBatchC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/adv_api/matmul/matmul_client.h
---

# GetBatchC

## 功能说明

[GetBatchTensorC](get_batch_tensor_c.md)接口与该接口的功能相同，建议使用[GetBatchTensorC](get_batch_tensor_c.md)。

调用一次GetBatchC，会获取C矩阵分片，该接口可以与[IterateNBatch](iterate_n_batch.md)异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max\(batchA, batchB\) \* singleCoreM \* singleCoreN大小的矩阵分片。

## 函数原型

```
template <bool sync = true>
__aicore__ inline GlobalTensor<DstT> GetBatchC(uint32_t batchA, uint32_t batchB, bool enSequentialWrite = false)
```

```
template <bool sync = true>
__aicore__ inline void GetBatchC(const LocalTensor<DstT>& c, uint32_t batchA, uint32_t batchB, bool enSequentialWrite = false)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| sync | 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false，默认为同步模式。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| batchA | 输入 | 左矩阵的batch数。 |
| batchB | 输入 | 右矩阵的batch数。 |
| enSequentialWrite | 输入 | 输出是否连续存放数据，默认false（非连续写模式）。 |
| c | 输入 | C矩阵，用于保存矩阵分片。类型为[LocalTensor](../../../basic_api/data_structures/local_tensor/index.md)。 |

## 返回值说明

GlobalTensor<DstT\>，返回计算的矩阵分片。

## 约束说明

当开启MixDualMaster（双主模式）场景时，即模板参数[enableMixDualMaster](matmul_config.md#matmulconfig-params)设置为true，不支持使用该接口。

## 调用示例

```
// 计算需要多Batch计算循环次数
int g_lay = tiling.ALayoutInfoG > tiling.BLayoutInfoG ? tiling.ALayoutInfoG : tiling.BLayoutInfoG;
int for_exent = tiling.ALayoutInfoB * tiling.ALayoutInfoN * g_lay / tiling.BatchNum;
mm1.SetTensorA(gm_a[0], isTransposeAIn);
mm1.SetTensorB(gm_b[0], isTransposeBIn);
if (tiling.isBias) {
    mm1.SetBias(gm_bias[0]);
}
// 多batch Matmul计算
mm1.template IterateNBatch<false>(for_exent, batchA, batchB, false);
// ...other compute
for (int i = 0; i < for_exent ; ++i) {
    mm1.template GetBatchC<false>(ubCmatrix, batchA, batchB);
    // ...other compute
}
```


<!-- cannbot:related:start -->
## 相关

- [IterateNBatch](iterate_n_batch.md)（`related`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。；IterateNBatch 异步生产多 Batch 结果，GetBatchC 的同功能替代接口负责逐片消费。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；调用一次GetBatchTensorC，会获取C矩阵片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；两端定义同一 C 分片获取合同，焦点还给出向 GetBatchTensorC 的明确迁移建议。
<!-- cannbot:related:end -->
