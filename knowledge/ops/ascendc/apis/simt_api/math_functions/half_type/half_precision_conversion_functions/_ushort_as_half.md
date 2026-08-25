---
type: API
title: __ushort_as_half
description: 将unsigned short int的数据按位重新解释为half，即将unsigned short int的数据存储的位按照half的格式进行读取。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__ushort_as_half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ushort_as_half

功能：将unsigned short int的数据按位重新解释为half，即将unsigned short int的数据存储的位按照half的格式进行读取。

函数原型：half __ushort_as_half(const unsigned short int x)

参数：x（输入）源操作数。

返回值：unsigned short int的数据按位重新解释为half的值。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→ASCRT_MIN_DENORM_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
