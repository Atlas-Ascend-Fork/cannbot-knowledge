---
type: API
title: __hcmadd
description: 将三个half2输入视为复数，第一个分量为实部，第二个分量为虚部，执行复数乘加运算x*y+z。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_arithmetic_functions/__hcmadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hcmadd

功能：将三个half2输入视为复数，第一个分量为实部，第二个分量为虚部，执行复数乘加运算x*y+z。

函数原型：half2 __hcmadd(const half2 x, const half2 y, const half2 z)

参数：x（输入）源操作数，y（输入）源操作数，z（输入）源操作数。

返回值：输入数据视为复数，执行复数乘加运算的结果。对于输入x、y、z的结果。特殊值：实部结果→虚部结果；__hfma(-x.y, y.y, __hfma(x.x, y.x, z.x))→__hfma(x.y, y.x, __hfma(x.x, y.y, z.y))。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
