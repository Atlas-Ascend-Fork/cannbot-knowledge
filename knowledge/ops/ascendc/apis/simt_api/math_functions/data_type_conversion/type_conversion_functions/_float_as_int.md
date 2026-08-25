---
type: API
title: __float_as_int
description: 将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float_as_int.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float_as_int

功能：将浮点数中的位重新解释为有符号整数，即将浮点数存储的位按照有符号整数的格式进行读取。

函数原型：int __float_as_int(const float x)

参数：x（输入）源操作数。

返回值：输入的浮点数中的位重新解释成的有符号整数。特殊值：0→0；-0→ASCRT_MIN_VAL_S；nan→2143289344；inf→ASCRT_INT32_INF_S；-inf→-8388608；ASCRT_MAX_NORMAL_F→2139095039；-ASCRT_MAX_NORMAL_F→-8388609。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
