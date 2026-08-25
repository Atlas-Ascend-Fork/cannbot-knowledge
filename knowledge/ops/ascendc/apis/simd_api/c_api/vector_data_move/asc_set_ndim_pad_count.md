---
type: API
title: AscSetNdimPadCount
description: 设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ndim_pad_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetNdimPadCount

用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。
函数原型：void asc_set_ndim_pad_count(asc_ndim_pad_count_config& config)
约束：需配合asc_ndim_copy_gm2ub使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
