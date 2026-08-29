---
type: API
title: __lows2half2
description: 分别提取两个half2输入的低16位，并填充到half2中，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__lows2half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __lows2half2

功能：分别提取两个half2输入的低16位，并填充到half2中，返回填充后的数据。

函数原型：half2 __lows2half2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：分别提取两个half2输入的低16位，并填充到half2的结果。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→ASCRT_MIN_DENORM_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
