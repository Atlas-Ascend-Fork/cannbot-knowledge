---
type: API
title: __float22bfloat162_ru
description: 将float2类型数据的两个分量遵循CAST_CEIL模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float22bfloat162_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22bfloat162_ru

将float2类型数据的两个分量遵循CAST_CEIL模式转换为bfloat16精度，返回转换后的bfloat16x2_t类型数据。
函数原型：bfloat16x2_t __float22bfloat162_ru(const float2 x)
返回值：将输入的两个分量遵循CAST_CEIL模式转换成的bfloat16x2_t类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
