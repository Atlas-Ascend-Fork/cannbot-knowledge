---
type: API
title: 逻辑计算
description: 寄存器侧逻辑计算类接口汇总，提供and、or、not、xor及左右移位等按位逻辑与移位操作。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/logic_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 逻辑计算

寄存器侧逻辑计算接口提供按位逻辑与移位运算。按位运算含asc_and/or/not/xor，移位运算含asc_shiftleft/shiftright及对应_scalar标量变体。
适用于掩码操作、位域处理和定点小数缩放等场景。
