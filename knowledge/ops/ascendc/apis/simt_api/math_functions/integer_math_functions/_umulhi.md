---
type: API
title: __umulhi
description: 获取输入uint32类型数据x和y乘积的高32位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__umulhi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __umulhi

uint32 高位乘法函数。获取输入 uint32 类型数据 x 和 y 乘积的高 32 位。

函数原型：unsigned int __umulhi(unsigned int x, unsigned int y)

参数 x、y 为源操作数（乘数）。返回乘积的高 32 位。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
