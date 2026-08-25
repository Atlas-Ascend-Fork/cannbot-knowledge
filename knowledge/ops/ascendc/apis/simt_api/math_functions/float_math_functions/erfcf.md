---
type: API
title: Erfcf
description: 获取输入数据的互补误差函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/erfcf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Erfcf

功能：获取输入数据的互补误差函数值。

函数原型：float erfcf(float x)

参数：x（输入）源操作数。

返回值：当x为nan时，返回值为nan；当x为inf时，返回值为0；当x为-inf时，返回值为2。特殊值：nan→nan；inf→0；-inf→2。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了exp2f，由于exp2f不支持Subnormal场景，在极少数场景下内部指数计算结果为Subnormal数据，导致本接口最终结果为0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
