---
type: API
title: SetBatchInfoForNormal
description: 设置A/B矩阵的M/N/K轴信息，以及A/B矩阵的Batch数。Layout类型为NORMAL的场景，调用IterateBatch或者IterateNBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A/B矩阵的M/N/K轴等信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBatchInfoForNormal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetBatchInfoForNormal

设置A/B矩阵的M/N/K轴信息，以及A/B矩阵的Batch数。Layout类型为NORMAL的场景，调用IterateBatch或者IterateNBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A/B矩阵的M/N/K轴等信息。

参数：
- batchA（输入）：A矩阵的batch数
- batchB（输入）：B矩阵的batch数
- m：输入A矩阵的M轴信息
- n：输入B矩阵的N轴信息
- k：输入A/B矩阵的K轴信息

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：Batch Matmul基础功能 与《SetBatchInfoForNormal》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [IterateNBatch](../matmul_kernel/iterate_n_batch.md)（`related`）：SetBatchInfoForNormal 明确是 IterateNBatch 前置 Host Tiling 配置，后者又要求 isNBatch、workspace 与完成等待策略，形成配置到执行的直接契约链。
- [SetBatchNum](../matmul_kernel/set_batch_num.md)（`related`）：SetBatchInfoForNormal说明设置A/B矩阵的M/N/K轴信息，以及A/B矩阵的Batch数。Layout类型为NORMAL的场景，调用IterateBatch或者IterateNBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A/B矩阵的M/N/K轴等信息；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [SetBatchNum](set_batch_num.md)（`related`）：《SetBatchInfoForNormal》明确“设置A/B矩阵的M/N/K轴信息，以及A/B矩阵的Batch数。Layout类型为NORMAL的场景，调用IterateBatch或者IterateNBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A/B矩阵的M/N/K轴等信息。”；它与《SetBatchNum》的“设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetBatchTensorC](../matmul_kernel/get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC 与《SetBatchInfoForNormal》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
<!-- cannbot:related:end -->
