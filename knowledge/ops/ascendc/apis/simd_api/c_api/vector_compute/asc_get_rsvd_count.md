---
type: API
title: AscGetRsvdCount
description: 此接口用于获取执行asc_reduce操作后剩余的元素数量。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_rsvd_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetRsvdCount

此接口用于获取执行asc_reduce操作后剩余的元素数量。
函数原型：int64_t asc_get_rsvd_count()
返回值：执行asc_reduce操作后剩余的元素数量。
约束：需和asc_reduce操作配合使用。；需通过同步操作确保asc_reduce执行完成后再调用本接口获取结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
