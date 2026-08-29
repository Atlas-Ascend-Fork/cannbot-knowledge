---
type: API
title: H2Floor
description: 获取小于或等于输入数据各元素的最大整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Floor

功能：获取小于或等于输入数据各元素的最大整数值。

函数原型：half2 h2floor(half2 x)

参数：x（输入）源操作数。

返回值：小于或等于输入数据各元素的最大整数值。本接口受全局饱和寄存器影响，。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16；ASCRT_MIN_DENORM_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
