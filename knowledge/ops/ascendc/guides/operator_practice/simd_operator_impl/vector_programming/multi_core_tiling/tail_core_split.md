---
type: Guide
title: TailCoreSplit
description: 主块均分后剩余数据无法以DataBlock均匀分配到每个核时，将额外DataBlock分配给前几个整核，其余为尾核，分别处理不同数据量。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/tail_core_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 尾核切分

在实际算子开发中，受输入数据总量与切分单位的制约，并非所有场景都能将计算完全均匀地分配到每个核上。该场景中，主块均分后存在剩余数据mainTileRemainder，但剩余数据无法以DataBlock为最小单位均匀分配到每个核（tailBlockNumEachCore为0，remainingTailLength不为0），只能继续分配给部分核。获得额外DataBlock的核为整核，其余为尾核；此时核间负载不均衡，需要分别处理整核和尾核。由于tailBlockNumEachCore为0，各核未分配到基础尾块，因此尾核内只包含主块，整核比尾核多处理一个DataBlock的尾块。数据切分后，前formerNum个核为整核，各处理formerLength个元素（含主块和尾块）；其余核为尾核，各处理tailLength个元素（仅含主块）。
本场景样例的完整代码请参考场景2：尾核切分。样例中固定使用8个核，主块长度mainTileLength为3200个half元素，数据整体长度为256064个half元素。数据按DataBlock对齐后，前4个核各处理32016个元素，后4个核各处理32000个元素；整核包含10个主块和16个元素的尾块，尾核只包含10个主块。数据切分示意如下图所示。
图 1  数据切分示意图
本场景中整核和尾核处理的元素数量、主块数量及尾块情况不同，无法仅用一组blockLength、tileNum和lastTileLength描述所有核。因此Tiling参数新增formerNum记录整核数量，并分别使用former*和tail*参数描述记录整核和尾核相关Tiling信息的参数；由于尾核内只包含主块，无需定义tailLastTileLength。Tiling结构体包含以下成员：
- formerNum：分配到数据量较多的核数，即整核的核数。
- formerLength：整核计算的元素数量。
- formerTileNum：整核中主块的数量。
- formerLastTileLength：整核中尾块的元素数量。
- tailLength：尾核计算的元素数量。
- tailTileNum：尾核中主块的数量。
## Tiling实现
Tiling结构体定义如下：
Host侧Tiling沿用尾块均分中的DataBlock对齐、主块分配和基础尾块计算，得到：按DataBlock均分后仍无法均分到每个核的剩余元素数量remainingTailLength、每个核分配到的DataBlock数量tailBlockNumEachCore、每个核基础尾块的元素数量baseLastTileLength、每个核已分配的基础元素数量baseLength，以及对应的主块数量baseTileNum。当remainingTailLength不为0时，尾块均分分支不成立，继续执行以下步骤：
1. remainingTailLength对应的剩余数据无法均分到每个核，只能分配给前formerNum个整核。

<!-- cannbot:related:start -->
## 相关

- [TailCoreTailBlockSplit](tail_core_tail_block_split.md)（`related`）：当remainingTailLength和tailBlockNumEachCore均不为0时，尾核切分分支不成立，进入尾核尾块切分场景。；由于tailBlockNumEachCore为0，各核未分配到基础尾块，因此尾核内只包含主块，整核比尾核多处理一个DataBlock的尾块。；两端以 tailBlockNumEachCore 是否为 0 划分互斥分支，前者必须记录尾核尾块，后者只给整核追加一个 DataBlock，直接决定 Tiling 字段和 Kernel 尾块处理。
- [SIMD算子实现主块均分](main_block_even_split.md)（`same_topic`）：“当mainTileRemainder为0时”定义无余数快路径，“tailBlockNumEachCore为0，remainingTailLength不为0”定义余数只能分给部分整核的分支，二者共同闭合多核切分选择。
<!-- cannbot:related:end -->
