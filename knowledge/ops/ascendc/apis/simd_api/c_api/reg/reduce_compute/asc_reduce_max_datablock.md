---
type: API
title: AscReduceMaxDatablock
description: 根据mask将每个DataBlock中的最大值依次保存在目的操作数的最低位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_max_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMaxDatablock

根据mask将每个DataBlock(32B)中的最大值依次保存在dst中的最低位。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 在比较中，遵循max(-0, +0) = +0。
- 找到源操作数中每个DataBlock内的最大值，连续写入到目的操作数，目的操作数中的其它元素置0。
- 未被mask选中的元素被视为最小值（浮点数为-inf），如果一个DataBlock中所有元素都未被mask选中，-inf将被填充到目的操作数的指定位置。
- 仅输出最值，不输出索引下标。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceMax](../../vector_compute/asc_datablock_reduce_max.md)（`related`）：两卡都对每个 32B DataBlock 求最大值；Memory C API 从 UB 输入，Reg API 在 mask 下把各块最大值连续写到 dst 低位并明确全 mask 块为 -inf。
- [AscReduceSumDatablock](asc_reduce_sum_datablock.md)（`related`）：Max/Min/Sum Datablock 共享粒度但聚合运算不同。
- [AscReduceMax](asc_reduce_max.md)（`same_topic`）：AscReduceMax 与《AscReduceMaxDatablock》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscReduceMinDatablock](asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceMaxDatablock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
<!-- cannbot:related:end -->
