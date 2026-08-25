---
type: API
title: H2Cos
description: 获取输入数据各元素的三角函数余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2cos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Cos

功能：获取输入数据各元素的三角函数余弦值。

函数原型：bfloat16x2_t h2cos(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各元素的三角函数余弦值。本接口受全局饱和模式影响，。特殊值：nan→0；inf→0；-inf→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
