---
type: API
title: AscGetCmpMask
description: 此接口用于获取Compare操作的比较结果。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_cmp_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetCmpMask

此接口用于获取Compare操作的比较结果。
函数原型：void asc_get_cmp_mask(__ubuf__ void* dst)
参数：dst（输出）：存放比较操作结果的地址。
约束：需和Compare操作配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
