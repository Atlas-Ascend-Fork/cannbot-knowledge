---
type: Guide
title: TailCoreTailBlockSplit
description: 主块均分后剩余DataBlock无法均分到每个核时，整核和尾核都包含尾块，整核比尾核多处理一个DataBlock，需分别记录Tiling参数。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/multi_core_tiling/tail_core_tail_block_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 尾核尾块切分

该场景中，主块均分后存在剩余数据mainTileRemainder，剩余数据部分能以DataBlock为最小单位均匀分配到每个核，但仍有少量DataBlock无法均分（remainingTailLength不为0），只能继续分配给部分核。获得额外DataBlock的核为整核，其余为尾核；整核和尾核都包含尾块，且整核处理的数据量更多。由于tailBlockNumEachCore不为0，各核都分配到基础尾块，因此尾核内也存在尾块；整核在尾核基础上多处理一个DataBlock。数据切分后，前formerNum个核为整核，各处理formerLength个元素（含主块和较长的尾块）；其余核为尾核，各处理tailLength个元素（含主块和较短的尾块）。
本场景样例的完整代码请参考场景3：尾核尾块切分。样例中固定使用8个核，主块长度mainTileLength为3200个half元素，数据整体长度为258112个half元素。数据按DataBlock对齐后，前4个核各处理32272个元素，后4个核各处理32256个元素；整核包含10个主块和272个元素的尾块，尾核包含10个主块和256个元素的尾块。数据切分示意如下图所示。
图 1  数据切分示意图
本场景中整核和尾核处理的元素数量、主块数量及尾块长度均不同，需要分别记录两类核的Tiling参数。与尾核切分相比，由于尾核内也存在尾块，Tiling参数在former*和tail*基础上新增tailLastTileLength记录尾核的尾块元素数量。Tiling结构体包含以下成员：
- formerNum：分配到数据量较多的核数，即整核的核数。
- formerLength：整核计算的元素数量。
- formerTileNum：整核中主块的数量。
- formerLastTileLength：整核中尾块的元素数量。
- tailLength：尾核计算的元素数量。
- tailTileNum：尾核中主块的数量。
- tailLastTileLength：尾核中尾块的元素数量。
## Tiling实现
Tiling结构体定义如下：
Host侧Tiling沿用尾核切分中的DataBlock对齐、主块分配、基础尾块计算及整核/尾核划分，得到：整核数量formerNum、每个整核处理的元素数量formerLength、每个尾核处理的元素数量tailLength、每个核基础尾块的元素数量baseLastTileLength、整核中主块的数量formerTileNum，以及尾核中主块的数量tailTileNum。当remainingTailLength和tailBlockNumEachCore均不为0时，尾核切分分支不成立，进入尾核尾块切分场景。此时整核比尾核多处理一个DataBlock，整核尾块长度formerLastTileLength为基础尾块长度baseLastTileLength与alignNum（一个DataBlock包含的half元素数量）之和；若两者之和等于mainTileLength，则将其合并为一个主块（formerTileNum加1，formerLastTileLength置0）。尾核尾块长度tailLastTileLength直接取baseLastTileLength。

<!-- cannbot:related:start -->
## 相关

- [TailCoreSplit](tail_core_split.md)（`related`）：当remainingTailLength和tailBlockNumEachCore均不为0时，尾核切分分支不成立，进入尾核尾块切分场景。；由于tailBlockNumEachCore为0，各核未分配到基础尾块，因此尾核内只包含主块，整核比尾核多处理一个DataBlock的尾块。；两端以 tailBlockNumEachCore 是否为 0 划分互斥分支，前者必须记录尾核尾块，后者只给整核追加一个 DataBlock，直接决定 Tiling 字段和 Kernel 尾块处理。
- [SIMD算子实现主块均分](main_block_even_split.md)（`same_topic`）：“当mainTileRemainder为0时”定义最简单的主块均分快路径，“remainingTailLength和tailBlockNumEachCore均不为0”定义整核与尾核都含尾块的最复杂分支，二者属于同一切分决策树。
<!-- cannbot:related:end -->
