---
type: API
title: Lgammaf
description: 获取输入数据x伽马值的绝对值并求自然对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/lgammaf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Lgammaf

功能：获取输入数据x伽马值的绝对值并求自然对数。

函数原型：float lgammaf(float x)

参数：x（输入）源操作数。

返回值：输入数据的伽马值的绝对值并求自然对数。特殊值：0→inf；inf→inf；-inf→inf；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Lgamma](../../../simd_api/adv_api/math_compute/lgamma_interface/lgamma.md)（`same_topic`）：功能：获取输入数据x伽马值的绝对值并求自然对数。；按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(｜gamma(x)｜)）。模板参数T支持half/float。两卡核心数学对象均为 lgamma，分别覆盖 SIMT 标量 float 与高阶 LocalTensor 逐元素接口。
<!-- cannbot:related:end -->
