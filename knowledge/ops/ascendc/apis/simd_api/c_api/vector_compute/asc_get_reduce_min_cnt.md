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
updated_at: '2026-08-27T12:23:11Z'
platforms: [a2, a3]
---

# AscGetReduceMinCnt

此接口用于获取执行asc_repeat_reduce_min操作后的最小值，以及第一个最小值时的索引。
函数原型：void asc_get_reduce_min_cnt(half& val, uint32_t& index)
约束：需和asc_repeat_reduce_min操作配合使用。；需通过同步操作确保asc_repeat_reduce_min执行完成后再调用本接口获取结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscRepeatReduceMin](asc_repeat_reduce_min.md)（`related`）：此接口用于获取执行asc_repeat_reduce_min操作后的最小值，以及第一个最小值时的索引。；对每个Repeat内所有元素求最小值，以及Repeat内的首个最小值元素在当前Repeat中的索引index。。结果读取接口的输入正是 asc_repeat_reduce_min 产出的最小值与首个索引，计算接口说明该结果在每个 Repeat 内的生成语义，二者构成归约计算到结果解释的调用链。
<!-- cannbot:related:end -->
