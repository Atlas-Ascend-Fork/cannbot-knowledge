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

- [AscReduceMax](../reg/reduce_compute/asc_reduce_max.md)（`same_topic`）：AscReduceMax 与《AscGetReduceMaxCnt》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscRepeatReduceMax](asc_repeat_reduce_max.md)（`same_topic`）：“AscRepeatReduceMax”处理对每个 Repeat 的元素求最大值，并返回首个最大值在该 Repeat 中的索引；一次 Repeat 处理 256 字节。；“AscGetReduceMaxCnt”明确此接口用于获取执行asc_repeat_reduce_max操作后的最大值，以及第一个最大值时的索引。。实质衔接：AscGetReduceMaxCnt 读取 AscRepeatReduceMax 保存的最大值和首个索引；RepeatReduceMin 是同一 repeat 契约下的最小值选择。
<!-- cannbot:related:end -->
