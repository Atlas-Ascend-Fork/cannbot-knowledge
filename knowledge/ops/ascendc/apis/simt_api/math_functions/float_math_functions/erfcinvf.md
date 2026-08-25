---
type: API
title: Erfcinvf
description: 获取输入数据的逆互补误差函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/erfcinvf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Erfcinvf

功能：获取输入数据的逆互补误差函数值。

函数原型：float erfcinvf(float x)

参数：x（输入）源操作数。

返回值：当x为0时，返回值为inf；当x为nan时，返回值为nan；当x为2时，返回值为-inf；当x∉[0,2]时，返回nan。特殊值：0→inf；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Erfinvf](erfinvf.md)（`related`）：《Erfinvf》的任务是“获取输入数据的逆误差函数值。”。《Erfcinvf》具体提供“获取输入数据的逆互补误差函数值。”，它直接用于逆误差函数与正向/互补逆函数的数值关系。
<!-- cannbot:related:end -->
