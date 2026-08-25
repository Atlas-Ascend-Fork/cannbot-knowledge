---
type: API
title: AscGetReduceMinCnt
description: 此接口用于获取执行asc_repeat_reduce_min操作后的最小值，以及第一个最小值时的索引。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_reduce_min_cnt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetReduceMinCnt

此接口用于获取执行asc_repeat_reduce_min操作后的最小值，以及第一个最小值时的索引。
函数原型：void asc_get_reduce_min_cnt(half& val, uint32_t& index)
约束：需和asc_repeat_reduce_min操作配合使用。；需通过同步操作确保asc_repeat_reduce_min执行完成后再调用本接口获取结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceMin](asc_datablock_reduce_min.md)（`related`）：GetReduceMinCnt 提供归约计数/辅助信息，和 DataBlockReduceMin 的最小值结果用途不同。
- [AscReduceMinDatablock](../reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscGetReduceMinCnt》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscRepeatReduceMin](asc_repeat_reduce_min.md)（`same_topic`）：AscGetReduceMinCnt 在同步后取回 RepeatReduceMin 产生的最小值和索引，是结果消费链的直接下一步。
- [ReduceMin](../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《AscGetReduceMinCnt》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
