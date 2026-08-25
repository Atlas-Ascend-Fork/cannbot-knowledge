---
type: API
title: 逻辑计算
description: Reg矢量计算逻辑运算接口索引页，汇总Not、And、Or、Xor及ShiftLeft/ShiftRight系列。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/logical_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 逻辑计算

Reg 矢量逻辑运算接口集合，作用于寄存器侧 Tensor。包含按位逻辑（Not、And、Or、Xor）与移位运算（ShiftLeft、ShiftRight，ShiftLefts/ShiftRights 为标量移位版本）。相比 Memory 版本新增 Xor 运算，结果直接保存在寄存器中。
