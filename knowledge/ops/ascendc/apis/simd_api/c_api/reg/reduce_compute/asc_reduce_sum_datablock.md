---
type: API
title: AscReduceSumDatablock
description: 根据mask将每个DataBlock中参与计算的元素相加，结果依次保存在目的操作数最低位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_sum_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscReduceSumDatablock

根据mask将每个DataBlock（32B）中参与计算的元素相加，并将最终的计算结果依次保存在dst的最低位。
约束：指令内累加顺序采用二叉树累加方式，在每个DataBlock（32B）内两两相加逐层归约求和，结果连续写入到目的操作数，目的操作数中的其它元素置0。；当DataBlock中的元素均不参与计算（mask全为0）时，将0写入dst对应位置（对于浮点数则为+0）。；对于输入为uint16_t/int16_t类型的情况，会提升精度到uint32_t/int32_t进行计算。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscReduceMaxDatablock](asc_reduce_max_datablock.md)（`related`）：Max/Min/Sum Datablock 共享粒度但聚合运算不同。
- [AscReduceSum](asc_reduce_sum.md)（`related`）：AscReduceSum 对整个 mask 选中集合输出单个和；Datablock 版本对每个 32B 块分别归约并连续输出，适合需要保留块级结果的路径。
- [AscRepeatReduceSum](../../vector_compute/asc_repeat_reduce_sum.md)（`related`）：RepeatReduceSum 跨 repeat 聚合，范围大于单 DataBlock。
- [ReduceDataBlock](../../../basic_api/reg_vector_compute/reduction_compute/reduce_data_block.md)（`related`）：C API 的 asc_reduce_sum_datablock 是 Reg ReduceDataBlock 的 SUM 专项入口，可在需要显式 C 风格寄存器与 mask 控制时映射同一块内求和。
- [AscDatablockReduceSum](../../vector_compute/asc_datablock_reduce_sum.md)（`same_topic`）：AscDatablockReduceSum 与《AscReduceSumDatablock》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceMinDatablock](asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceSumDatablock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
<!-- cannbot:related:end -->
