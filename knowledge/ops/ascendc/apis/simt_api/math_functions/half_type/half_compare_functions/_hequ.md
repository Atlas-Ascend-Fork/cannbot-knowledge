---
type: API
title: __hequ
description: 比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hequ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequ

功能：比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。

函数原型：bool __hequ(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据是否相等的结果。特殊值：±0→true；inf→true；-inf→true；inf→false；-inf→false；ASCRT_MAX_NORMAL_FP16→true；ASCRT_MAX_NORMAL_FP16→false；(1,ASCRT_MAX_NORMAL_FP16)→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
