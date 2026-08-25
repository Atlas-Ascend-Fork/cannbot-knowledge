---
type: API
title: __half2uint_rd
description: 遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2uint_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2uint_rd

功能：遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。

函数原型：unsigned int __half2uint_rd(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的无符号整数。特殊值：±0→0；nan→0；inf→4294967295（uint32_t最大值）；-inf→0；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→0；ASCRT_MIN_DENORM_FP16→0；0.5→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
