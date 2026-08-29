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

- [Batch Matmul基础功能](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/batch_matmul_basics.md)（`explains`）：通过IterateBatch接口批量处理Matmul，可以有效提升带宽利用率。；调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；指南给出小 shape 批处理的性能动机，API 卡给出一次调用产生多个 C 矩阵的执行合同。
- [IterateNBatch](iterate_n_batch.md)（`related`）：单次Matmul计算处理的shape比较小时，由于每次计算均涉及到内部的通信，可能会影响性能，该接口提供批量处理Matmul的功能，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。；IterateNBatch 直接以 IterateBatch 为单次计算单元，并新增 isNBatch 与 workspace 输出合同。
- [SetBatchNum](set_batch_num.md)（`related`）：在不改变Tiling的情况下，重新设置多Batch计算的Batch数。；调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；SetBatchNum 调整当前 Matmul 对象的 batchA/batchB，随后 IterateBatch 按该多 Batch 状态一次产出多个 C 矩阵，形成运行期批数设置到批量执行的调用链。
- [SetBatchNum](../matmul_tiling/set_batch_num.md)（`related`）：“调用IterateBatch接口之前，需要在Host侧Tiling实现中通过本接口设置多Batch计算的Batch数”；“调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵”。SetBatchNum 生产 IterateBatch 必需的 Batch Tiling 参数，后者按该参数批量计算。
- [WaitIterateBatch](wait_iterate_batch.md)（`related`）：“等待IterateBatch异步接口或IterateNBatch异步接口返回，支持连续输出到Global Memory。”与“异步场景需要配合WaitIterateBatch接口使用。”分别给出两端正文事实；WaitIterateBatch 是 IterateBatch 异步提交的明确等待端，联合阅读可确定 sync/waitIterateBatch 参数与完成点的正确组合。
<!-- cannbot:related:end -->
