---
type: API
title: Erfcxf
description: 获取输入数据的缩放互补误差函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/erfcxf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Erfcxf

功能：获取输入数据的缩放互补误差函数值。

函数原型：float erfcxf(float x)

参数：x（输入）源操作数。

返回值：当x为0时，返回值为1；当x为nan时，返回值为nan；当x为-inf时，返回值为inf；当x为inf时，返回0。特殊值：0→1；nan→nan；-inf→inf。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，在极少数场景下内部计算的除法结果为Subnormal数据，导致本接口最终结果为0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
