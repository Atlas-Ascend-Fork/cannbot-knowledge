---
type: API
title: __high2half
description: 提取输入half2的高16位，并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__high2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __high2half

功能：提取输入half2的高16位，并返回。

函数原型：half __high2half(const half2 x)

参数：x（输入）源操作数。

返回值：返回输入half2的高16位。特殊值：±0→±0；nan→nan；±inf→±inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
