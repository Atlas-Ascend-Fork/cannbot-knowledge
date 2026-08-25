---
type: API
title: WaitIterateBatch
description: 等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitIterateBatch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# WaitIterateBatch

等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。

函数原型：__aicore__ inline void WaitIterateBatch()

约束：
- 配套IterateBatch或IterateNBatch异步接口使用。
- 仅支持连续输出至Global Memory。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBatchC](get_batch_c.md)（`related`）：GetBatchC 与《WaitIterateBatch》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [IterateBatch](iterate_batch.md)（`related`）：IterateBatch 的异步模板参数 waitIterateBatch=true 明确要求用 WaitIterateBatch 等待批量 Matmul 完成；目标卡是该等待动作的直接生产端。
- [SetBatchNum](set_batch_num.md)（`related`）：WaitIterateBatch说明等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC 与《WaitIterateBatch》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
- [Iterate](iterate.md)（`same_topic`）：Iterate 与《WaitIterateBatch》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch 与《WaitIterateBatch》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
<!-- cannbot:related:end -->
