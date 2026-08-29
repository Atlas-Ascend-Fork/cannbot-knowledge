---
type: API
title: min（整数数学函数）
description: 获取两个输入数据中的最小值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# min

通用最小值函数（模板重载）。获取两个输入数据中的最小值，支持 long long、long、int、short、char 及对应 unsigned 类型的重载。

函数原型示例：long long min(long long x, long long y)、int min(int x, int y)、unsigned int min(unsigned int x, unsigned int y) 等共 10 种重载。

参数 x、y 为源操作数。返回输入数据中的最小值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/math_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。
