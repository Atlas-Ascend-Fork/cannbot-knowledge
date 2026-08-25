---
type: API
title: __hbgtux2
description: 比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbgtux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgtux2

功能：比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbgtux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于第二个数的结果。特殊值：((nan, nan),(nan, nan))→true；((nan, 正常值),(正常值, nan))→true；((inf, inf),(有限值, 有限值))→true；((-inf, -inf),(有限正数, 有限正数))→false；((有限正数, 有限正数),(inf, inf))→true；((inf, inf),(-inf, -inf))→true；((±0, ±0),(±0, ±0))→false；((有限值, 有限值),(有限值, 有限值))→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
