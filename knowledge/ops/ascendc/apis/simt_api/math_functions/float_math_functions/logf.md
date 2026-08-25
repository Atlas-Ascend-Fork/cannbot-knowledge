---
type: API
title: 数学函数logf
description: 获取以e为底，输入数据的对数。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/logf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数logf

功能：获取以e为底，输入数据的对数。

函数原型：float logf(float x)

参数：x（输入）源操作数。

返回值：以e为底的x的对数。特殊值：nan→nan；0→-inf；inf→inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Log1pf](log1pf.md)（`related`）：《数学函数logf》说明获取以e为底，输入数据的对数。；《Log1pf》说明计算ln(1+x)，在x接近0时比直接log(1+x)保持更高精度。。二者在logf是直接自然对数，而log1pf在x接近0时实现同一数学量的稳定形式上存在可执行的直接衔接。
<!-- cannbot:related:end -->
