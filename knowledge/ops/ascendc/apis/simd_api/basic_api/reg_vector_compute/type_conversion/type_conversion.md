---
type: API
title: 类型转换
description: 寄存器矢量类型转换接口集合，包含Cast和Truncate接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/type_conversion/type_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 类型转换

提供 Cast 和 Truncate 两个寄存器级类型转换接口。Cast 支持浮点转整数、浮点转浮点、整数转浮点、整数转整数四种转换，可通过 RegLayout、SatMode、MaskMergeMode、RoundMode 控制转换行为。

Truncate 将浮点数元素截断为整数值，保持原数据类型不变，支持 CAST_RINT、CAST_ROUND、CAST_FLOOR、CAST_CEIL、CAST_TRUNC 舍入模式，当前仅支持 ZEROING 模式。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
