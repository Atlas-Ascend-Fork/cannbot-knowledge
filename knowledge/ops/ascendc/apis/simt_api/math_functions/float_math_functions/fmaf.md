---
type: API
title: 数学函数fmaf
description: 对输入数据x、y、z，计算x与y相乘加上z的结果。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/fmaf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数fmaf

功能：对输入数据x、y、z，计算x与y相乘加上z的结果。

函数原型：float fmaf(float x, float y, float z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：x * y + z的值。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
