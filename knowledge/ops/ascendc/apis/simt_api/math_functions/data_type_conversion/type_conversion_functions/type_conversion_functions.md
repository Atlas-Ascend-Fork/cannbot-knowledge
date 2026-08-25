---
type: API
title: 类型转换函数
description: 提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/type_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 类型转换函数

提供 float 与 int、uint、ll、ull 等整型之间的双向类型转换，支持 rn、rz、rd、ru、rna 五种舍入模式。还包含 __float_as_int、__float_as_uint、__int_as_float、__uint_as_float 等位级重新解释函数，在不改变底层比特表示的前提下完成类型映射。适用于 SIMT 编程模型下的精确类型控制场景。
