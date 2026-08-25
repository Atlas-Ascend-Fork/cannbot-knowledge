---
type: API
title: H2Sqrt
description: 获取输入数据x各元素的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Sqrt

功能：获取输入数据x各元素的平方根。

函数原型：bfloat16x2_t h2sqrt(bfloat16x2_t x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据各元素的平方根。本接口受全局饱和模式影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→0。

约束：本接口支持的输入数据各元素范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
