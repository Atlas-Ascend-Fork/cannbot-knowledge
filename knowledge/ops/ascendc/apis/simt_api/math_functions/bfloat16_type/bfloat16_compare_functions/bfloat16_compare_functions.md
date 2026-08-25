---
type: API
title: bfloat16类型比较函数
description: bfloat16类型比较函数集合，包括最大最小值、无穷与NaN判断及有序和无序比较运算。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/bfloat16_compare_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# bfloat16类型比较函数

提供bfloat16类型的标量比较运算函数。极值与判断含__hmax/__hmin及__hisnan/__hisinf（NaN/无穷判断）。
有序比较含__heq/__hne/__hle/__hge/__hlt/__hgt，无序比较含__hequ/__hneu/__hleu/__hgeu/__hltu/__hgtu（无序版本在存在NaN时返回特定值）。
__hmax_nan/__hmin_nan在操作数为NaN时返回NaN而非另一操作数。函数以双下划线前缀命名，遵循SIMT标量数学函数命名规范。
