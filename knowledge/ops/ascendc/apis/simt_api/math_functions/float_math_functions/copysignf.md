---
type: API
title: Copysignf
description: 获取由第一个输入x的数值部分和第二个输入y的符号部分拼接得到的浮点数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/copysignf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Copysignf

功能：获取由第一个输入x的数值部分和第二个输入y的符号部分拼接得到的浮点数。

函数原型：float copysignf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：y>=0时，返回x的绝对值Abs(x)；y<0时，返回x绝对值的相反数，-Abs(x)；y=nan时，返回-Abs(x)；y=-inf时，返回-Abs(x)；y=inf时，返回Abs(x)。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
