---
type: API
title: __floats2half2_rn
description: 将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__floats2half2_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __floats2half2_rn

功能：将输入数据x、y遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分，返回转换后的half2类型数据。

函数原型：half2 __floats2half2_rn(const float x, const float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：将输入float类型数据遵循CAST_RINT模式分别转换为half类型，并填充到half2的前后两部分的结果。本接口受全局饱和寄存器影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
