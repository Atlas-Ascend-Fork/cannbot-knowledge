---
type: API
title: __ll2float_rz
description: 遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__ll2float_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2float_rz

功能：遵循CAST_TRUNC模式，将int64类型数据转换为浮点数，返回转换后的值。

函数原型：float __ll2float_rz(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_TRUNC模式转换成的浮点数。特殊值：0→0；16777217（2^24+1 ）→ASCRT_TWO_TO_24_F；-16777217（-2^24-1）→-ASCRT_TWO_TO_24_F；9223372036854775807（INT64_MAX）→9.22337149e+18；-9223372036854775808（INT64_MIN）→-9.22337204e+18。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
