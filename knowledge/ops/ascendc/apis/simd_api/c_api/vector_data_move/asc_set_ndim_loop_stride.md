---
type: API
title: AscSetNdimLoopStride
description: 设置asc_ndim_copy_gm2ub接口每个维度内源和目的操作数元素间的间隔，最多5个维度。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ndim_loop_stride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetNdimLoopStride

用于设置asc_ndim_copy_gm2ub接口，每个维度内的源操作数与目的操作数的元素之间的间隔，最多设置5个维度。
函数原型：void asc_set_ndim_loop0_stride(uint64_t dst_stride, uint64_t src_stride)
约束：需配合asc_ndim_copy_gm2ub使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
