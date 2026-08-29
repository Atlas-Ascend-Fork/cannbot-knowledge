---
type: API
title: __hfma_relu
description: 对输入bfloat16类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__hfma_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hfma_relu

对输入bfloat16类型数据x、y、z，计算x与y相乘加上z的结果，并遵循CAST_RINT模式对结果进行舍入。负数结果置为0。
函数原型：bfloat16_t __hfma_relu(const bfloat16_t x, const bfloat16_t y, const bfloat16_t z)
返回值：x \ y + z的值。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
