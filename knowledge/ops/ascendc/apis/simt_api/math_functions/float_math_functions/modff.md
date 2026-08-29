---
type: API
title: Modff
description: 将输入参数分解为小数部分和整数部分。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/modff.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Modff

功能：将输入参数分解为小数部分和整数部分。

函数原型：float modff(float x, float *n)

参数：x（输入）源操作数，n（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储输入数据的整数部分。

返回值：输入参数的小数部分。特殊值：nan→nan；inf→0；-inf→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
