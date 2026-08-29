---
type: API
title: llabs（整数数学函数）
description: 获取输入数据的绝对值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/llabs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# llabs

long long 类型绝对值函数。获取输入数据的绝对值。

函数原型：inline long long int llabs(long long int x)

参数 x 为源操作数。返回输入数据的绝对值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
