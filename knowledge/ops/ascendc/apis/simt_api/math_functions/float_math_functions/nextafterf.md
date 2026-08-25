---
type: API
title: Nextafterf
description: 返回从x朝向y方向的下一个可表示浮点值，若x等于y则返回x。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/nextafterf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Nextafterf

功能：对于两个数据x、y： 如果y大于x，返回比x大的下一个可表示的浮点值。 如果y小于x，返回比x小的下一个可表示的浮点值。 如果y等于x，返回x。

函数原型：float nextafterf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：x不等于y时，返回y方向上x之后下一个可表示的浮点值；x等于y时，返回x；若x、y任意一个为nan，返回nan；若x=+inf，y不为nan，返回3.4028235e+38；若x=-inf，y不为nan，返回-3.4028235e+38。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
