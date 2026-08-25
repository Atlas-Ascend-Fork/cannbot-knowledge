---
type: API
title: AscDatablockReduceSum
description: 对每个 DataBlock 内的元素按二叉树方式求和；half 累加中间结果超过 65504 时按 65504 保存。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_datablock_reduce_sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscDatablockReduceSum

对每个DataBlock内所有元素求和。 源操作数相加采用二叉树的方式，两两相加。以128个half类型数据求和为例，每个DataBlock可以计算16个half类型数据，分成8个DataBlock计算；每个DataBlock内，通过二叉树的方式，两两相加。 需要注意的是，两两相加计算过程中，计算结果大于65504时结果保存为65504。例如，源操作数为[60000,60000,-30000,100]，首先60000+60000溢出，结果为65504，然后计算-30000+100=-29900，最后计算65504-29900=35604。
函数原型：void asc_datablock_reduce_sum(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceMax](asc_datablock_reduce_max.md)（`related`）：AscDatablockReduceSum 与《AscDatablockReduceMax》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscDatablockReduceMin](asc_datablock_reduce_min.md)（`related`）：AscDatablockReduceSum 与《AscDatablockReduceMin》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscRepeatReduceSum](asc_repeat_reduce_sum.md)（`related`）：AscDatablockReduceSum 使用相同二叉树和 half 65504 中间饱和规则，但按 32B DataBlock 而非整 Repeat 输出和。
- [GetDataBlockSizeInBytes](../../basic_api/tool_interface/system_resources_and_variables/get_data_block_size_in_bytes.md)（`related`）：AscDatablockReduceSum 与《GetDataBlockSizeInBytes》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceSumDatablock](../reg/reduce_compute/asc_reduce_sum_datablock.md)（`same_topic`）：AscDatablockReduceSum 与《AscReduceSumDatablock》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [ReduceDataBlock](../../basic_api/memory_vector_compute/reduction_compute/reduce_data_block.md)（`same_topic`）：AscDatablockReduceSum 与《ReduceDataBlock》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [ReduceDataBlock](../../basic_api/reg_vector_compute/reduction_compute/reduce_data_block.md)（`same_topic`）：AscDatablockReduceSum 与《ReduceDataBlock》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [ReduceSum](../../basic_api/memory_vector_compute/reduction_compute/reduce_sum.md)（`same_topic`）：AscDatablockReduceSum 与《ReduceSum》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
<!-- cannbot:related:end -->
