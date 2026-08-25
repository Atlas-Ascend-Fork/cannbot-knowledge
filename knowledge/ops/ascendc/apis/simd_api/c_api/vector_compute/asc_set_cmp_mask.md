---
type: API
title: AscSetCmpMask
description: 为asc_select操作设置作用于选择的Mask掩码。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_cmp_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetCmpMask

为asc_select操作设置作用于选择的Mask掩码。
函数原型：void asc_set_cmp_mask(__ubuf__ void* sel_mask)
参数：sel_mask（输入）：用于选择的Mask掩码的起始地址。
约束：需和asc_select操作配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
