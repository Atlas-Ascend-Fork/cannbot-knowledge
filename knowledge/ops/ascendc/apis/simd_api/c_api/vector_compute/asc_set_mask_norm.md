---
type: API
title: AscSetMaskNorm
description: 设置Mask模式为Normal模式，该模式为系统默认模式。该模式下，Mask参数可控制高维切分计算过程中单次迭代内参与计算的元素。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_mask_norm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetMaskNorm

设置Mask模式为Normal模式，该模式为系统默认模式。该模式下，Mask参数可控制高维切分计算过程中单次迭代内参与计算的元素。
函数原型：void asc_set_mask_norm()
约束：该API需和asc_set_vector_mask配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetVectorMask](asc_set_vector_mask.md)（`same_topic`）：AscSetMaskNorm 明确“约束：该API需和asc_set_vector_mask配合使用。”；AscSetVectorMask 同时要求“约束：需先调用asc_set_mask_count或asc_set_mask_norm设置Mask模式。”，双方定义的是同一 Vector Mask 配置序列中的模式选择与 mask 值设置合同。
<!-- cannbot:related:end -->
