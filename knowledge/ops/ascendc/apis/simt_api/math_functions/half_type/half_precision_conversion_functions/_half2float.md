---
type: API
title: __half2float
description: 将half类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2float

功能：将half类型数据转换为浮点数，返回转换后的值。

函数原型：float __half2float(const half x)

参数：x（输入）源操作数。

返回值：输入转换成的浮点数。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
