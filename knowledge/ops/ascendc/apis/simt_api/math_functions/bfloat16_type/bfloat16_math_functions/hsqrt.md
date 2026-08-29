---
type: API
title: Hsqrt
description: 计算bfloat16_t输入数据x的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/hsqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hsqrt

获取输入数据x的平方根。
函数原型：bfloat16_t hsqrt(bfloat16_t x)
返回值：输入数据的平方根。本接口受全局饱和模式影响，特殊值如下：
约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。；针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
