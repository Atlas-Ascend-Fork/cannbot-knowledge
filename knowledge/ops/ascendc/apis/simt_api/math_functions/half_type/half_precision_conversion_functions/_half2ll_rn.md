---
type: API
title: __half2ll_rn
description: 遵循CAST_RINT模式，将half类型数据转换为long long类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2ll_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2ll_rn

功能：遵循CAST_RINT模式，将half类型数据转换为long long类型数据，返回转换后的值。

函数原型：long long int __half2ll_rn(const half x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_RINT模式转换成的long long类型数据。特殊值：±0→0；nan→0；inf→9223372036854775807（long long最大值）；-inf→-9223372036854775808（long long最小值）；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；±0.5→0；2.5→2。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
