---
type: API
title: __ull2float_rna
description: 遵循CAST_ROUND模式，将uint64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ull2float_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ull2float_rna

功能：遵循CAST_ROUND模式，将uint64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ull2float_rna(const unsigned long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的浮点数。特殊值：0→0；16777217（2^24+1）→16777218；33554431（2^25-1）→33554432；33554434（2^25+2）→33554436；18446744073709551615（ULLONG_MAX）→1.84467441e+19。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
