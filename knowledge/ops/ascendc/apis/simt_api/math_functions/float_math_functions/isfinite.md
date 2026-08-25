---
type: API
title: Isfinite
description: 判断浮点数是否为有限数（非inf、非nan）。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isfinite.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Isfinite

功能：判断浮点数是否为有限数（非inf、非nan）。

函数原型：bool isfinite(float x)

参数：x（输入）源操作数。

返回值：false：输入为nan、inf、-inf；true：输入为有限数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsFinite](../../../simd_api/adv_api/math_compute/is_finite_interface/is_finite.md)（`same_topic`）：高阶 IsFinite 与 SIMT isfinite 都判断 float 是否非 NaN 且非 ±Inf，分别输出 tensor 布尔/数值结果与标量 bool。
<!-- cannbot:related:end -->
