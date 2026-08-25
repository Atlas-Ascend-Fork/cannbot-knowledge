---
type: Guide
title: SIMD算子实现尾块均分
description: 该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/tail_block_even_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 尾块均分

该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。
本场景样例的完整代码请参考场景1：尾块均分。样例中固定使用8个核，主块长度mainTileLength为3200个half元素，数据整体长度为260096个half元素。数据平均分配到8个核上处理，每个核计算32512个元素；每个核内包含10个主块和512个元素的尾块。数据切分示意如下图所示。
图 1  数据切分示意图
与主块均分相比，本场景每个核内除主块外还存在尾块，因此Tiling参数在blockLength和tileNum基础上新增lastTileLength，用于记录尾块的元素数量。
## Tiling实现
算子的Tiling结构体定义如下：
Host侧Tiling沿用主块均分中的DataBlock对齐和主块分配计算，得到：主块均分后的剩余元素数量mainTileRemainder、每个核已分配的基础元素数量baseLength、以及对应的主块数量baseTileNum。当mainTileRemainder不为0时，主块均分分支不成立，继续执行以下步骤：
1. 以DataBlock为最小单位，将主块均分后的剩余数据mainTileRemainder均匀分配到每个核上。一个DataBlock包含alignNum个half元素，因此代码中以alignNum作为均分的单位。用mainTileRemainder除以numBlocks * alignNum得到每个核分配到的DataBlock数量tailBlockNumEachCore，取余得到按DataBlock均分后仍无法均分到每个核的剩余元素数量remainingTailLength；再将tailBlockNumEachCore乘以alignNum得到每个核基础尾块的元素数量baseLastTileLength，并累加到baseLength上得到每个核的基础元素数量。
2. 判断remainingTailLength是否为0。等于0表示mainTileRemainder能以DataBlock为最小单位均匀分配到每个核，此时进入尾块均分场景，使用MainTileWithTailBlockTiling结构体传递Tiling切分信息。
对形状为(1, 260096)的输入数据计算后，Tiling结构体内各个变量的值如下：
## 算子类实现
Kernel侧算子仍采用静态Tensor编程方式实现。与主块均分相比，本场景中每个核处理的数据长度仍相同，因此Global Memory偏移仍由tiling.blockLength和GetBlockIdx()计算；差异在于Init函数需要额外保存tiling.lastTileLength，供Process函数判断最后一次循环是否处理尾块。

<!-- cannbot:related:start -->
## 相关

- [GetBlockIdx](../../../../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（`explains`）：《GetBlockIdx》处理“获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。”。《SIMD算子实现尾块均分》明确提供“该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。”，其参数、调用或验证步骤直接接入GetBlockIdx/GetBlockNum 与 Tiling 切核、尾核边界和多核验证的合同。
- [DoubleBuffer场景](../double_buffer_scenario.md)（`related`）：DoubleBuffer场景 与《SIMD算子实现尾块均分》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [SIMD算子实现概述](overview.md)（`related`）：尾块均分处理总块数不能整除核数时的负载分配，补充主块策略的尾部情况。
- [基础矢量算子](../basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《SIMD算子实现尾块均分》说明该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [SIMD算子实现主块均分](main_block_even_split.md)（`same_topic`）：《SIMD算子实现主块均分》说明长度为totalLength的输入数据可以按参与计算的核数和主块长度mainTileLength均匀切分，主块均分后无剩余数据。各核处理的数据量相同，每个核处理tileNum个主块，核内只包含主块。；《SIMD算子实现尾块均分》说明该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockNumEachCore个DataBlock的数据，且按DataBlock均分后无剩余。最终各核处理的数据量相同，核内除主块外还存在等长尾块。。二者在主块均分与三种尾块策略共同覆盖多核切分分支；Kernel用GetBlockIdx定位GM段，numBlocks塌缩故障验证Host切核结果上存在可执行的直接衔接。
- [TailCoreSplit](tail_core_split.md)（`same_topic`）：“SIMD算子实现尾块均分”处理该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockN…；“TailCoreSplit”明确主块均分后剩余数据无法以DataBlock均匀分配到每个核时，将额外DataBlock分配给前几个整核，其余为尾核，分别处理不同数据量。。实质衔接：主块均分、尾块均分、尾核切分按 remainder 是否存在及能否按 DataBlock 均分构成同一可执行分支决策。
- [TailCoreTailBlockSplit](tail_core_tail_block_split.md)（`same_topic`）：“SIMD算子实现尾块均分”处理该场景中，完成主块分配后仍有剩余数据，但剩余数据无法继续按主块均匀分配到每个核。为了均衡利用多核计算能力，继续以DataBlock为最小单位将主块均分后剩余数据mainTileRemainder均衡分配到每个核，每个核分配到tailBlockN…；“TailCoreTailBlockSplit”明确主块均分后剩余DataBlock无法均分到每个核时，整核和尾核都包含尾块，整核比尾核多处理一个DataBlock，需分别记录Tiling参数。。实质衔接：主块均分、尾块均分、尾核切分按 remainder 是否存在及能否按 DataBlock 均分构成同一可执行分支决策。
<!-- cannbot:related:end -->
