---
type: API
title: AscPairReduceSum
description: 对输入数据做归约操作，得到数据总和。相邻两个（奇偶）元素求和，例如（a1，a2，a3，a4，a5，a6…），相邻两个数据求和为（a1+a2，a3+a4，a5+a6…）。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_pair_reduce_sum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscPairReduceSum

对输入数据做归约操作，得到数据总和。相邻两个（奇偶）元素求和，例如（a1，a2，a3，a4，a5，a6…），相邻两个数据求和为（a1+a2，a3+a4，a5+a6…）。
函数原型：void asc_pair_reduce_sum(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscRepeatReduceSum](asc_repeat_reduce_sum.md)（`related`）：AscPairReduceSum 只合并相邻奇偶元素，可作为多级归约中的局部一步；AscRepeatReduceSum 则在 Repeat 内完成完整树形求和。
- [PairReduceElem](../../basic_api/reg_vector_compute/reduction_compute/pair_reduce_elem.md)（`related`）：PairReduceElem 是 C++ Reg API 对应的相邻元素规约能力，为从 C API 迁移提供语义等价入口。
- [ReduceSum](../../basic_api/memory_vector_compute/reduction_compute/reduce_sum.md)（`related`）：PairReduceSum 只完成一层相邻元素折叠，完整标量求和还需继续规约，ReduceSum 描述最终归约能力。
- [AscPairReduceSum](../reg/reduce_compute/asc_pair_reduce_sum.md)（`same_topic`）：Vector 与 Reg C API 都做相邻元素 pair-sum，但输入驻留和结果布局不同，可按编程路径映射。
<!-- cannbot:related:end -->
