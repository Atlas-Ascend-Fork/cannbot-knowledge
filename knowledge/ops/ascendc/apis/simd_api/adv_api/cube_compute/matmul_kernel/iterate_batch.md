---
type: API
title: IterateBatch
description: 批量处理Matmul的接口，调用一次可计算出多个singleCoreM*singleCoreN大小的C矩阵。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/IterateBatch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# IterateBatch

单次Matmul计算处理的shape比较小时，由于每次计算均涉及到内部的通信，可能会影响性能，该接口提供批量处理Matmul的功能，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。 在使用该接口前，需要了解一些必备的数据排布格式： - 通用数据格式（NORMAL）：BMNK的数据排布格式；B：Batch，批处理的大小；M、、N、K为矩阵乘\[M, K\]\*\[K, N\]的矩阵维度；其数据排布格式如下：

函数原型：template <bool sync = true, bool waitIterateBatch = false>

参数：
- sync：获取C矩阵过程分为同步和异步两种模式：同步：需要同步等待IterateBatch执行结束。 异步：不需要同步等待IterateBatch执行结束。 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。异步场景需要配合WaitIterateBatch接口使用。
- waitIterateBatch：是否需要通过WaitIterateBatch接口等待IterateBatch执行结束，仅在异步场景下使用。默认为false。 true：需要通过WaitIterateBatch接口等待IterateBatch执行结束。 false：不需要通过WaitIterateBatch接口等待IterateBatch执行结束，开发者自行处理等待IterateBatch执行结束的过程。
- gm（输出）：C矩阵。类型为GlobalTensor。不同型号支持的数据类型请参考支持的数据类型。

约束：
- 该接口只支持Norm模板，即BatchMatmul只支持Norm模板。
- 使用该接口时，A、B矩阵的Layout格式必须相同。
- 对于BSNGD、SBNGD、BNGS1S2 Layout格式，输入A、B矩阵按分形对齐后的多Batch数据总和应小于L1 Buffer的大小；对于NORMAL  Layout格式没有这种限制，但需通过MatmulConfig配置输入A、B矩阵多Batch数据大小与L1 Buffer的大小关系；

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：Batch Matmul基础功能 与《IterateBatch》的实质衔接是：Batch Matmul 直接使用 Batch tmp 查询、IterateBatch/NBatch、batch shape/输出与 batch 数配置；workspace 和精度卡约束真实使用。
- [SetBatchNum](set_batch_num.md)（`related`）：IterateBatch说明批量处理Matmul的接口，调用一次可计算出多个singleCoreM*singleCoreN大小的C矩阵；对SetBatchNum而言，Batch 数配置决定 IterateBatch/IterateNBatch 的输入布局与循环次数；异步批处理还必须由 WaitIterateBatch 闭合生命周期。
- [SetCLayout](../matmul_tiling/set_c_layout.md)（`related`）：SetCLayout 文档明确要求 BSNGD、SBNGD、BNGS1S2 布局在调用 IterateBatch 前设置 C 的 B/S/N/G/D 轴信息。
- [WaitIterateBatch](wait_iterate_batch.md)（`related`）：IterateBatch 的异步模板参数 waitIterateBatch=true 明确要求用 WaitIterateBatch 等待批量 Matmul 完成；目标卡是该等待动作的直接生产端。
- [GetBatchC](get_batch_c.md)（`same_topic`）：GetBatchC 与《IterateBatch》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [Iterate](iterate.md)（`same_topic`）：Iterate 与《IterateBatch》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch 与《IterateBatch》的实质衔接是：IterateNBatch 必须先开启 MatmulConfig::isNBatch、配置 Host 侧 batch 信息并申请 workspace；同步/异步结果分别经 WaitIterateBatch 或 GetBatchTensorC/GetBatchC 获取，使用说明给出完整调用顺序。
<!-- cannbot:related:end -->
