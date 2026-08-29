---
type: API
title: __float2ll_rz
description: 遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ll_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ll_rz

功能：遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。

函数原型：long long int __float2ll_rz(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的64位有符号整数。特殊值：±0→0；nan→0；inf→9223372036854775807（INT64_MAX）；-inf→-9223372036854775808（INT64_MIN）；超出int64范围的正值→9223372036854775807（INT64_MAX）；超出int64范围的负值→-9223372036854775808（INT64_MIN）。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
