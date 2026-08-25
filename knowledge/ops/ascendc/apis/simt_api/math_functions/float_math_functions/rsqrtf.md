---
type: API
title: Rsqrtf
description: 获取输入数据x的平方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rsqrtf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rsqrtf

功能：获取输入数据x的平方根的倒数。

函数原型：float rsqrtf(float x)

参数：x（输入）源操作数，输入数据。

返回值：输入数据的平方根的倒数。特殊值：0→inf；inf→0；-inf→nan；nan→nan。

约束：本接口支持的输入数据范围为x大于等于0，否则返回值为nan。 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
