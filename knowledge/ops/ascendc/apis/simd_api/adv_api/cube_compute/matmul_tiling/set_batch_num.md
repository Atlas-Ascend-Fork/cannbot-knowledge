---
type: API
title: SetBatchNum
description: 设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBatchNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetBatchNum

设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。

参数：
- batch（输入）：多Batch计算的Batch数，Batch数为A矩阵batchA和B矩阵batchB中的最大值。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [IterateBatch](../matmul_kernel/iterate_batch.md)（`related`）：“调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数”；“调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵”。SetBatchNum 生产 IterateBatch 必需的 Batch Tiling 参数，后者按该参数批量计算。
- [SetBatchNum](../matmul_kernel/set_batch_num.md)（`related`）：在不改变Tiling的情况下，重新设置多Batch计算的Batch数。；设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。；Host 侧先把最大 Batch 写入 Tiling，Kernel 侧再在不重做 Tiling 时改当前 batchA/batchB，二者是同一 Matmul 多 Batch 配置在静态上限与运行期覆盖两个阶段的合同。
<!-- cannbot:related:end -->
