---
type: API
title: half类型精度转换函数
description: 提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/half_precision_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# half类型精度转换函数

提供 half 与 float、bfloat16、int、uint、ll、ull 等类型之间的双向精度转换，支持 rn、rz、rd、ru、rna 五种舍入模式及 ro 舍入变体，部分函数提供 _sat 饱和版本。还包含 half2 向量类型的拆分与组合函数（__high2half、__low2half、__halves2half2 等）和位级重解释函数 __ushort_as_half。
