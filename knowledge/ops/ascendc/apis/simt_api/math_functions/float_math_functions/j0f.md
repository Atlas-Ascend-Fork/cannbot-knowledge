---
type: API
title: 数学函数j0f
description: 获取输入数据x的0阶第一类贝塞尔函数j0的值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/j0f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数j0f

功能：获取输入数据x的0阶第一类贝塞尔函数j0的值。贝塞尔函数常用于波动方程和圆柱坐标系问题的求解。

函数原型：float j0f(float x)

参数：x（输入）源操作数。

返回值：输入数据的0阶第一类贝塞尔函数j0的值。返回值范围为[-1, 1]。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
