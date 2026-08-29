---
type: API
title: __bfloat162bfloat162
description: 将输入数据填充为bfloat16x2前后两个分量，返回转换后的bfloat16x2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162bfloat162

将输入数据填充为bfloat16x2前后两个分量，返回转换后的bfloat16x2类型数据。
函数原型：bfloat16x2_t __bfloat162bfloat162(const bfloat16_t x)
返回值：输入的数据填充为bfloat16x2的数据。特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
