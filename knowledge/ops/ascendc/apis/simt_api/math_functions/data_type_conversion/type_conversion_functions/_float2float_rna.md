---
type: API
title: __float2float_rna
description: 将浮点数四舍五入取整，并遵循CAST_ROUND模式。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2float_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2float_rna

功能：将浮点数四舍五入取整，并遵循CAST_ROUND模式。

函数原型：float __float2float_rna(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式取整后的浮点数。特殊值：±0→0；nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
