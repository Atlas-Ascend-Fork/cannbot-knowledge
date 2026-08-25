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

<!-- cannbot:related:start -->
## 相关

- [half类型精度转换函数](../../half_type/half_precision_conversion_functions/half_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《bfloat16类型精度转换函数》说明bfloat16类型精度转换函数列表，包含bfloat16与float、half、int、uint、ull等类型间的相互转换。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [类型转换函数](../../data_type_conversion/type_conversion_functions/type_conversion_functions.md)（`related`）：bfloat16类型精度转换函数 与《类型转换函数》的实质衔接是：该页概括 bfloat16 与 float/half/整数的双向转换及五种舍入，通用类型转换页和精度舍入规则补充模式语义，half 转换页提供同一转换矩阵在另一低精度类型上的对照。
- [精度转换（数据结构）](../../../../simd_api/basic_api/data_structures/precision_conversion.md)（`related`）：bfloat16类型精度转换函数 与《精度转换（数据结构）》的实质衔接是：该页概括 bfloat16 与 float/half/整数的双向转换及五种舍入，通用类型转换页和精度舍入规则补充模式语义，half 转换页提供同一转换矩阵在另一低精度类型上的对照。
<!-- cannbot:related:end -->
