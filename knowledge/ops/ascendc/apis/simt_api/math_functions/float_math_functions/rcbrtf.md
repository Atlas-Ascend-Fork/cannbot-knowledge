---
type: API
title: Rcbrtf
description: 获取输入数据x的立方根的倒数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rcbrtf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Rcbrtf

功能：获取输入数据x的立方根的倒数。

函数原型：float rcbrtf(float x)

参数：x（输入）源操作数。

返回值：x的立方根的倒数。特殊值：0→inf；nan→nan；inf→0；-inf→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Cbrtf](cbrtf.md)（`related`）：Cbrtf 与《Rcbrtf》的实质衔接是：Cbrtf 与 Rcbrtf 是立方根/倒立方根成对数学语义，float 数学函数页给出头文件与标量调用边界。
<!-- cannbot:related:end -->
