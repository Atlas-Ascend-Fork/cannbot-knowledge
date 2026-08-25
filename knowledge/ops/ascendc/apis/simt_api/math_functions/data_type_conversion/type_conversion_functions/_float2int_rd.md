---
type: API
title: __float2int_rd
description: 遵循CAST_FLOOR模式，将浮点数转换为有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2int_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2int_rd

功能：遵循CAST_FLOOR模式，将浮点数转换为有符号整数，返回转换后的值。

函数原型：int __float2int_rd(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的有符号整数。特殊值：±0→0；nan→0；inf→2147483647；-inf→-2147483648；超出 int 范围的正数→2147483647；超出 int 范围的负数→-2147483648；正小数→向下取整。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
