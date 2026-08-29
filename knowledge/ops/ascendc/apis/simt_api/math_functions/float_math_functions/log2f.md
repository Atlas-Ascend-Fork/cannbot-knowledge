---
type: API
title: Log2f
description: 获取以2为底输入数据的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log2f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log2f

功能：获取以2为底，输入数据的对数。

函数原型：float log2f(float x)

参数：x（输入）源操作数。

返回值：以2为底的x的对数。特殊值：inf→inf；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
