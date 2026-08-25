---
type: API
title: __clz（整数数学函数）
description: 从输入数据的二进制最高有效位开始，返回连续的前导零的位数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__clz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __clz

前导零计数函数。从输入数据的二进制最高有效位开始，返回连续的前导零的位数。

函数原型（重载）：int __clz(int x)、int __clz(long long x)、int __clz(long x)

参数 x 为源操作数。返回输入整数二进制表示中连续高位零的数量。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
