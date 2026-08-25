---
type: API
title: 数学函数jnf
description: 获取输入数据x的n阶第一类贝塞尔函数jn的值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/jnf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数jnf

功能：获取输入数据x的n阶第一类贝塞尔函数jn的值。

函数原型：float jnf(int n, float x)

参数：n（输入）源操作数，x（输入）源操作数。

返回值：输入数据的n阶第一类贝塞尔函数jn的值。

约束：- n的最大取值为128。 - 针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了expf，由于expf不支持Subnormal场景，在极少数场景下内部计算的expf结果为Subnormal数据，导致本接口最终结果为0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
