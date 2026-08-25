---
type: API
title: H2Sqrt
description: 获取输入数据x各元素的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Sqrt

功能：获取输入数据x各元素的平方根。

函数原型：half2 h2sqrt(half2 x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的平方根。本接口受全局饱和寄存器影响，。特殊值：0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→0。

约束：本接口支持的输入数据各元素范围为x大于等于0，否则返回值为nan。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
