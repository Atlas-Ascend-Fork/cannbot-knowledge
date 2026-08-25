---
type: API
title: H2Trunc
description: 获取对输入数据各元素的浮点数截断后的整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2trunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Trunc

功能：获取对输入数据各元素的浮点数截断后的整数。

函数原型：bfloat16x2_t h2trunc(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各元素的浮点数截断后的整数。本接口受全局饱和模式影响，。特殊值：0→0；-0→0；nan→0；inf→ASCRT_MAX_NORMAL_BF16；-inf→ASCRT_MIN_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
