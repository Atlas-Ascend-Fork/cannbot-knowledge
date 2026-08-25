---
type: API
title: __sad（整数数学函数）
description: 对输入数据x、y、z，计算 x - y + z的结果，即前两个输入作差的绝对值与第三个输入的和。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__sad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __sad

绝对差之和函数（有符号）。对输入数据 x、y、z 计算 |x - y| + z 的结果。

函数原型：unsigned int __sad(int x, int y, unsigned int z)

参数 x、y 为源操作数（int32_t），z 为源操作数（uint32_t）。返回 |x - y| + z。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
