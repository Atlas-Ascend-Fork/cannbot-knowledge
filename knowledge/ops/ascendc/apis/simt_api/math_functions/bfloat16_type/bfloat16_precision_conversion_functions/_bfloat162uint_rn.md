---
type: API
title: __bfloat162uint_rn
description: 遵循CAST_RINT模式，将bfloat16类型数据转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162uint_rn.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162uint_rn

遵循CAST_RINT模式，将bfloat16类型数据转换为无符号整数，返回转换后的值。
函数原型：unsigned int __bfloat162uint_rn(const bfloat16_t x)
返回值：输入遵循CAST_RINT模式转换成的无符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
