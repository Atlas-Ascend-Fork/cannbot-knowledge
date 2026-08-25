---
type: API
title: bfloat16类型算术函数
description: bfloat16类型算术函数集合，包括绝对值、乘加、加减乘除、取反及融合ReLU的乘加运算。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/bfloat16_arithmetic_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16类型算术函数

提供bfloat16类型的标量算术运算函数。四则运算含__hadd/__hsub/__hmul/__hdiv，绝对值__habs，取反__hneg。
融合运算含__hfma（融合乘加 a*b+c）和__hfma_relu（融合乘加并接ReLU激活）。函数以双下划线前缀命名，遵循SIMT标量数学函数命名规范。
