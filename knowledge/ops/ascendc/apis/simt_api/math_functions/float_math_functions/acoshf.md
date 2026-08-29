---
type: API
title: Acoshf
description: 获取输入数据的双曲反余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/acoshf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Acoshf

功能：获取输入数据的双曲反余弦值。

函数原型：float acoshf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲反余弦值。特殊值：inf→inf；-inf→nan；nan→nan。

约束：本接口支持的输入数据为[1, 65504.0]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
