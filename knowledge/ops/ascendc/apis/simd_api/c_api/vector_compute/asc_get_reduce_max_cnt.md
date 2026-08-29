---
type: API
title: AscGetReduceMaxCnt
description: 此接口用于获取执行asc_repeat_reduce_max操作后的最大值，以及第一个最大值时的索引。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_reduce_max_cnt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetReduceMaxCnt

此接口用于获取执行asc_repeat_reduce_max操作后的最大值，以及第一个最大值时的索引。
函数原型：void asc_get_reduce_max_cnt(half& val, uint32_t& index)
约束：需和asc_repeat_reduce_max操作配合使用。；需通过同步操作确保asc_repeat_reduce_max执行完成后再调用本接口获取结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscRepeatReduceMax](asc_repeat_reduce_max.md)（`related`）：此接口用于获取执行asc_repeat_reduce_max操作后的最大值，以及第一个最大值时的索引。；对每个Repeat内所有元素求最大值，以及Repeat内的首个最大值元素在当前Repeat中的索引index。一次Repeat计算256字节。。GetReduceMaxCnt 明确读取 AscRepeatReduceMax 的执行结果，目标接口定义每个 Repeat 产生的最大值与首个索引，因此二者构成先归约、再提取结果的调用链。
<!-- cannbot:related:end -->
