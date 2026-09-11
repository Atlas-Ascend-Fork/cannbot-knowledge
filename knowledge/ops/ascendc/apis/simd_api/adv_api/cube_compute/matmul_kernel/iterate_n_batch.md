---
type: API
title: IterateNBatch
description: 调用一次进行N次IterateBatch计算，支持多Batch输入多Batch输出，结果输出至SetWorkspace指定的Global
  Memory。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/IterateNBatch.md
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

# IterateNBatch

## 功能说明

调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM \* singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的[isNBatch](matmul_config.md#matmulconfig-params)参数设为true，开启多Batch输入多Batch输出功能，并调用[SetWorkspace](set_workspace.md)接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至[SetWorkspace](set_workspace.md)指定的Global Memory内存中。

对于BSNGD、SBNGD、BNGS1S2的Layout格式，调用该接口之前需要在tiling中使用SetALayout/SetBLayout/SetCLayout/SetBatchNum设置A/B/C的Layout轴信息和最大BatchNum数；对于Normal数据格式则需使用[SetBatchInfoForNormal](../matmul_tiling/set_batch_info_for_normal.md)设置A/B/C的M/N/K轴信息和A/B矩阵的BatchNum数。实例化Matmul时，通过MatmulType设置Layout类型，当前支持3种Layout类型：BSNGD、SBNGD、BNGS1S2。

## 函数原型

```
template <bool sync = true, bool waitIterateBatch = false>
__aicore__ inline void IterateNBatch(const uint32_t batchLoop, uint32_t batchA, uint32_t batchB, bool enSequentialWrite, const uint32_t matrixStrideA = 0, const uint32_t matrixStrideB = 0, const uint32_t matrixStrideC = 0)
```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| sync | 获取C矩阵过程分为同步和异步两种模式：<br>同步：需要同步等待IterateNBatch执行结束，后续由开发者自行获取输出到Global Memory上的计算结果。<br>异步：不需要同步等待IterateNBatch执行结束。<br><br>通过该参数设置同步或者异步模式：同步模式设置为true；异步模式设置为false。默认为同步模式。 |
| waitIterateBatch | 是否需要通过[WaitIterateBatch](wait_iterate_batch.md)接口等待IterateNBatch执行结束，仅在异步场景下使用。默认为false。<br><br>true：需要通过WaitIterateBatch接口等待IterateNBatch执行结束，然后由开发者自行获取输出到Global Memory上的计算结果。<br><br>false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用[GetBatchTensorC](get_batch_tensor_c.md)接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。 |

**表2**  接口参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| batchLoop | 输入 | 当前计算的BMM个数。 |
| batchA | 输入 | 当前单次BMM调用计算左矩阵的batch数。 |
| batchB | 输入 | 当前单次BMM调用计算右矩阵的batch数，brc场景batchA/B不相同。 |
| enSequentialWrite | 输入 | 输出是否连续存放数据。 |
| matrixStrideA | 输入 | A矩阵源操作数相邻nd矩阵起始地址间的偏移，默认值是0。 |
| matrixStrideB | 输入 | B矩阵源操作数相邻nd矩阵起始地址间的偏移，默认值是0。 |
| matrixStrideC | 输入 | 该参数预留，保持默认值0即可。 |

## 返回值说明

无

## 约束说明

-   单BMM内计算遵循之前的约束条件。
-   对于BSNGD、SBNGD、BNGS1S2 Layout格式，输入A、B矩阵多Batch数据总和应小于L1 Buffer的大小。
-   当开启MixDualMaster（双主模式）场景时，即模板参数[enableMixDualMaster](matmul_config.md#matmulconfig-params)设置为true，不支持使用该接口。
-   当使用ND格式输入，且单个BMM内A或B矩阵的[源矩阵内轴](iterate_batch.md#row_width)大于65535时，需在MatmulConfig中设置intrinsicsCheck为true。开启此选项后，API会将一次从Global Memory到L1 Buffer的ND2NZ搬运操作拆分为多次循环搬运，从而避免单次搬运指令参数超限。



## 调用示例

实例功能：完成aGM、bGM矩阵乘，结果保存到cGm上，其中aGM数据的layout格式为BSNGD，bGM数据的layout格式为BSNGD，cGM的layout格式为BNGS1S2，左矩阵每次计算batchA个SD数据，右矩阵每次计算batchB个SD数据。

```
// 创建Matmul实例
AscendC::Matmul<aType, bType, cType, biasType> mm1;
AscendC::TPipe pipe;
g_cubeTPipePtr = &pipe;

REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm1);
mm1.Init(&tiling);
int g_lay = tiling.ALayoutInfoG > tiling.BLayoutInfoG ? tiling.ALayoutInfoG : tiling.BLayoutInfoG;
int for_extent = tiling.ALayoutInfoB * tiling.ALayoutInfoN * g_lay / tiling.BatchNum;
mm1.SetTensorA(gm_a[0], isTransposeAIn);
mm1.SetTensorB(gm_b[0], isTransposeBIn);
mm1.SetWorkspace(workspaceGM, 0);
if (tiling.isBias) {
    mm1.SetBias(gm_bias[0]);
}
// 多batch Matmul计算
mm1.IterateNBatch(for_extent, batchA, batchB, false);
```


<!-- cannbot:related:start -->
## 相关

- [GetBatchC](get_batch_c.md)（`related`）：GetBatchTensorC接口与该接口的功能相同，建议使用GetBatchTensorC。 调用一次GetBatchC，会获取C矩阵分片，该接口可以与IterateNBatch异步接口配合使用。用于在调用IterateNBatch迭代计算后，获取一片std::max(batchA, batchB) * singleCoreM * singleCoreN大小的矩阵分片。；false：不需要通过WaitIterateBatch接口等待IterateNBatch执行结束。调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。；IterateNBatch 异步生产多 Batch 结果，GetBatchC 的同功能替代接口负责逐片消费。
- [Iterate](iterate.md)（`related`）：“每调用一次Iterate，会计算出一块baseM * baseN的C矩阵。接口内部会维护迭代进度，调用一次后会对A、B矩阵首地址进行偏移。”与“调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。”分别来自双方当前正文。Iterate 给出单次分块矩阵乘及内部进度推进，IterateNBatch 则把同一迭代模型扩展为多 Batch，并增加 isNBatch 与 SetWorkspace 前置合同；对照两卡可决定单块或批量执行路径。
- [IterateBatch](iterate_batch.md)（`related`）：单次Matmul计算处理的shape比较小时，由于每次计算均涉及到内部的通信，可能会影响性能，该接口提供批量处理Matmul的功能，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C矩阵。；调用一次IterateNBatch，会进行N次IterateBatch计算，计算出N个多Batch的singleCoreM * singleCoreN大小的C矩阵。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。；IterateNBatch 直接以 IterateBatch 为单次计算单元，并新增 isNBatch 与 workspace 输出合同。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：该接口可以与IterateNBatch异步接口配合使用；调用本接口后，需要调用GetBatchTensorC接口获取C矩阵，或者由开发者自行处理等待IterateNBatch执行结束的过程。GetBatchTensorC 定义异步结果分片的获取，IterateNBatch 明确在 waitIterateBatch=false 路径调用该接口，形成生产与取回 C 矩阵的直接调用合同。
- [SetWorkspace](set_workspace.md)（`same_topic`）：IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。SetWorkspace 卡定义缓存结果的 GM 空间，IterateNBatch 卡把这块空间列为调用前置并规定结果写入位置；二者构成同一次多 Batch Matmul 调用的资源申请和输出合同。
<!-- cannbot:related:end -->
