---
type: API
title: MaskReg计算
description: MaskReg计算接口索引页，包含Move、Interleave、DeInterleave、Select、Pack、UnPack与MoveMask。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/MaskReg_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MaskReg计算

MaskReg 专用计算接口集合，对掩码寄存器进行操作。Move 实现掩码数据搬运；Interleave/DeInterleave 实现交错与反交错；Select 按掩码选择；Pack/UnPack 实现打包与解包；MoveMask 移动掩码位。用于配合矢量计算的掩码控制，实现复杂的数据筛选与重排。
