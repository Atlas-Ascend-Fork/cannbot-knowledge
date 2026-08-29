---
type: API
title: bfloat16类型精度转换函数
description: bfloat16类型精度转换函数列表，包含bfloat16与float、half、int、uint、ull等类型间的相互转换。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/bfloat16_precision_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16类型精度转换函数

提供 bfloat16 与 float、half、int、uint、ll、ull 等类型之间的双向精度转换。转换支持 rn（就近舍入）、rz（向零舍入）、rd（向下舍入）、ru（向上舍入）、rna（就近偶数舍入）五种舍入模式，部分函数提供 _sat 饱和变体。还包含 bfloat16x2 向量类型的拆分与组合函数，如 __high2bfloat16、__low2bfloat16、__halves2bfloat162 等。
