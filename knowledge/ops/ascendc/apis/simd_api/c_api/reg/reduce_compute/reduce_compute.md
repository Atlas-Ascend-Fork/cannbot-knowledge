---
type: API
title: 归约计算
description: 寄存器侧归约计算类接口汇总，提供sum、max、min等逐元素及DataBlock级归约能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/reduce_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 归约计算

寄存器侧归约计算接口提供矢量数据的规约运算。asc_reduce_sum/max/min执行常规归约，asc_reduce_sum_datablock/max_datablock/min_datablock执行DataBlock级归约。
asc_pair_reduce_sum执行成对求和，适用于需要减少舍入误差的累加场景。

<!-- cannbot:related:start -->
## 相关

- [Memory矢量计算](../../vector_compute/memory_vector_compute.md)（`same_topic`）：归约计算 与《Memory矢量计算》的实质衔接是：Reg 归约索引与 Memory 归约索引分别汇总同一 sum/max/min/datablock 能力，接口成员关系由 part_of 覆盖。
- [归约计算](../../../basic_api/memory_vector_compute/reduction_compute/reduction_compute.md)（`same_topic`）：归约计算 与《归约计算》的实质衔接是：Reg 归约索引与 Memory 归约索引分别汇总同一 sum/max/min/datablock 能力，接口成员关系由 part_of 覆盖。
<!-- cannbot:related:end -->
