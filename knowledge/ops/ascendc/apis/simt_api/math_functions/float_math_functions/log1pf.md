---
type: API
title: Log1pf
description: 获取以e为底输入数据加1的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log1pf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log1pf

功能：获取以e为底，输入数据加1的对数（即ln(x+1)），可避免x接近0时的精度损失。

函数原型：float log1pf(float x)

参数：x（输入）源操作数。

返回值：以e为底的x+1的对数。特殊值：nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
