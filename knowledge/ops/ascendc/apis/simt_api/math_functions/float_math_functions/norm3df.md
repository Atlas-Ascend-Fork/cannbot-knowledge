---
type: API
title: Norm3df
description: 获取输入数据a、b、c平方和的平方根。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/norm3df.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Norm3df

功能：获取输入数据a、b、c的平方和a^2 + b^2 + c^2的平方根。

函数原型：float norm3df(float a, float b, float c)

参数：a（输入）源操作数，b（输入）源操作数，c（输入）源操作数。

返回值：a^2 + b^2 + c^2的平方根。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，当所有输入均为Subnormal数据时，本接口最终返回nan。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
