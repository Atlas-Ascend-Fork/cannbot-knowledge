---
type: API
title: Atanf
description: 获取输入数据的反正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/atanf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Atanf

功能：获取输入数据的反正切值。

函数原型：float atanf(float x)

参数：x（输入）源操作数。

返回值：输入数据的反正切值。特殊值：inf→π/2；-inf→-π/2；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
