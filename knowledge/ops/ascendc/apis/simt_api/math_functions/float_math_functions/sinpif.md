---
type: API
title: Sinpif
description: 获取输入数据与π相乘的正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/sinpif.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Sinpif

功能：获取输入数据与π相乘的正弦值。

函数原型：float sinpif(float x)

参数：x（输入）源操作数。

返回值：输入数据与π相乘的正弦值。特殊值：inf→nan；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Sincospif](sincospif.md)（`same_topic`）：Sinpif 是 Sincospif 的第一个输出；后者在同一输入上同时计算 sin(pi*x) 与 cos(pi*x)，可直接复用特殊值和 π 缩放验证。
<!-- cannbot:related:end -->
