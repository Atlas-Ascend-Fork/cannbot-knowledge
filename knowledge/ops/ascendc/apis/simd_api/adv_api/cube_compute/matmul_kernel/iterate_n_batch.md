---
type: API
title: IterateNBatch
description: 调用一次进行N次IterateBatch计算，支持多Batch输入多Batch输出，结果输出至SetWorkspace指定的Global Memory。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/IterateNBatch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# IterateNBatch

调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。

函数原型：template <bool sync = true, bool waitIterateBatch = false>

参数：
- sync：获取C矩阵过程分为同步和异步两种模式：同步：需要同步等待IterateNBatch执行结束，后续由开发者自行获取输出到Global Memory上的计算结果。 异步：不需要同步等待IterateNBatch执行结束。 通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。
- waitIterateBatch：是否需要通过[WaitIterateBatch接口等待IterateNBatch执行结束，仅在异步场景下使用。默认为false。 true：需要通过WaitIterateBatch接口等待IterateNBatch执行结束，然后由开发者自行获取输出到Global Memory上的计算结果。 false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。
- batchLoop（输入）：当前计算的BMM个数。

约束：
- 单BMM内计算遵循之前的约束条件。
- 对于BSNGD、SBNGD、BNGS1S2 Layout格式，输入A、B矩阵多Batch数据总和应小于L1 Buffer的大小。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [GetBatchC](get_batch_c.md)（`related`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。；IterateNBatch 异步生产多 Batch 结果，GetBatchC 的同功能替代接口负责逐片消费。
- [Iterate](iterate.md)（`related`）：“每调用一次Iterate，会计算出一块baseM * baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。”与“调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。”分别来自双方当前正文。Iterate 给出单次分块矩阵乘及内部进度推进，IterateNBatch 则把同一迭代模型扩展为多 Batch，并增加 isNBatch 与 SetWorkspace 前置合同；对照两卡可决定单块或批量执行路径。
- [IterateBatch](iterate_batch.md)（`related`）：单次Matmul计算处理的shape比较小时，由于每次计算均涉及到内部的通信，可能会影响性能，该接口提供批量处理Matmul的功能，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。；IterateNBatch 直接以 IterateBatch 为单次计算单元，并新增 isNBatch 与 workspace 输出合同。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：该接口可以与IterateNBatch异步接口配合使用；调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。GetBatchTensorC 定义异步结果分片的获取，IterateNBatch 明确在 waitIterateBatch=false 路径调用该接口，形成生产与取回 C 矩阵的直接调用合同。
- [SetWorkspace](set_workspace.md)（`same_topic`）：IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。SetWorkspace 卡定义缓存结果的 GM 空间，IterateNBatch 卡把这块空间列为调用前置并规定结果写入位置；二者构成同一次多 Batch Matmul 调用的资源申请和输出合同。
<!-- cannbot:related:end -->
