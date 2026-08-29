---
type: API
title: __half22float2
description: 将half2的两个分量分别转换为float，填充到float2后返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half22float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half22float2

功能：将half2的两个分量分别转换为float，填充到float2后返回。

函数原型：float2 __half22float2(const half2 x)

参数：x（输入）源操作数。

返回值：将half2的两个分量分别转换为float，并填充到float2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。


支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
