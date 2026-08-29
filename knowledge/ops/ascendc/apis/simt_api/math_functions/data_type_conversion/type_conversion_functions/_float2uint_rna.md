---
type: API
title: __float2uint_rna
description: 遵循CAST_ROUND模式，将浮点数转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2uint_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2uint_rna

功能：遵循CAST_ROUND模式，将浮点数转换为无符号整数，返回转换后的值。

函数原型：unsigned int __float2uint_rna(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的无符号整数。特殊值：±0→0；nan→0；inf→4294967295；-inf→0；超出uint32_t范围的正值→4294967295；负数→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
