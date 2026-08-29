---
type: API
title: __hblex2
description: 比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hblex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hblex2

功能：比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时返回true。

函数原型：bool __hblex2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数小于或等于第二个数的结果。特殊值：nan→false；(正常值,nan)→false；nan→false；0→true；-0→true；inf→true；-inf→true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
