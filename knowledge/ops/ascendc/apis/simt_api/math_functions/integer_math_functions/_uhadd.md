---
type: API
title: __uhadd（整数数学函数）
description: 获取uint32类型数据x和y的平均值，避免中间求和溢出。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__uhadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __uhadd

uint32 无符号平均值函数。获取 uint32 类型数据 x 和 y 的平均值，避免中间求和溢出（向下取整）。

函数原型：unsigned int __uhadd(unsigned int x, unsigned int y)

参数 x、y 为源操作数。返回输入数据的平均值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
