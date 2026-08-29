---
type: API
title: Scalblnf
description: 获取输入数据x与2的n次方的乘积。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/scalblnf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Scalblnf

功能：获取输入数据x与2的n次方的乘积。

函数原型：float scalblnf(float x, int64_t n)

参数：x（输入）源操作数，n（输入）源操作数。

返回值：输入数据x乘以2的n次幂的结果。特殊值：nan→nan；inf→inf；-inf→-inf。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了除法运算符，由于除法运算符不支持Subnormal场景，在极少数场景下内部计算的除法结果为Subnormal数据，导致本接口最终结果为0。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Scalbnf](scalbnf.md)（`same_topic`）：函数原型：float scalblnf(float x, int64_t n)；函数原型：float scalbnf(float x, int32_t n)。两接口都计算 x 与 2 的 n 次幂乘积，核心差异是指数 n 的 int64_t 与 int32_t 位宽，直接支撑按指数范围选择入口。
<!-- cannbot:related:end -->
