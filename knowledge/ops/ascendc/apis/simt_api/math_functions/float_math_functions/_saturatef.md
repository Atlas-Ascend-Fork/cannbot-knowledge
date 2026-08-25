---
type: API
title: __saturatef
description: 将输入数据转换至0.0到1.0区间。小于等于0返回0，大于等于1返回1，区间内返回原值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/__saturatef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __saturatef

功能：将输入数据转换至[0.0, 1.0]区间。具体来说，若输入数据大于或等于1，则结果为1，若输入数据小于或等于0，则结果为0，若输入数据在[0.0, 1.0]区间，则结果为原输入数据。

函数原型：float __saturatef(float x)

参数：x（输入）源操作数。

返回值：输入数据转换至[0.0, 1.0]区间的结果。特殊值：nan→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
