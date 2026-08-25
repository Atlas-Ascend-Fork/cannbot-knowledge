---
type: API
title: __ull2float_rd
description: 遵循CAST_FLOOR模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_rd

功能：遵循CAST_FLOOR模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_rd(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777216.0；4294967295（UINT32_MAX）→4294967040.0；18446744073709551615（UINT64_MAX）→2^64−2^40。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
