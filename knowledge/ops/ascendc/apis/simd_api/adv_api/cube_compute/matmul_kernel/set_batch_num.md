---
type: API
title: SetBatchNum
description: 在不改变Tiling的情况下，重新设置多Batch计算的Batch数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetBatchNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetBatchNum

在不改变Tiling的情况下，重新设置多Batch计算的Batch数。

函数原型：__aicore__ inline void SetBatchNum(int32_t batchA, int32_t batchB)

参数：
- batchA（输入）：设置的一次计算的A矩阵Batch数。
- batchB（输入）：设置的一次计算的B矩阵Batch数。

约束：
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。
- 本接口仅支持在纯Cube模式（只有矩阵计算）下调用。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [IterateBatch](iterate_batch.md)（`related`）：IterateBatch说明批量处理Matmul的接口，调用一次可计算出多个singleCoreM*singleCoreN大小的C矩阵；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [IterateNBatch](iterate_n_batch.md)（`related`）：IterateNBatch 与《SetBatchNum》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
- [SetBatchInfoForNormal](../matmul_tiling/set_batch_info_for_normal.md)（`related`）：SetBatchInfoForNormal说明设置A/B矩阵的M/N/K轴信息，以及A/B矩阵的Batch数。Layout类型为NORMAL的场景，调用IterateBatch或者IterateNBatch接口之前，需要在Host侧Tiling实现中通过本接口设置A/B矩阵的M/N/K轴等信息；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [WaitIterateBatch](wait_iterate_batch.md)（`related`）：WaitIterateBatch说明等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [GetBatchC](get_batch_c.md)（`same_topic`）：GetBatchC 与《SetBatchNum》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [SetBatchNum](../matmul_tiling/set_batch_num.md)（`same_topic`）：《SetBatchNum》明确“在不改变Tiling的情况下，重新设置多Batch计算的Batch数。”；它与《SetBatchNum》的“设置多Batch计算的最大Batch数，最大Batch数为A矩阵batchA和B矩阵batchB中的最大值。调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
