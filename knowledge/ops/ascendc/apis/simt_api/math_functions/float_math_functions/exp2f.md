---
type: API
title: Exp2f
description: 指定输入x，获取2的x次方。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/exp2f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Exp2f

功能：指定输入x，获取2的x次方。

函数原型：float exp2f(float x)

参数：x（输入）源操作数。

返回值：2的x次方。特殊值：inf→inf；-inf→0；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
