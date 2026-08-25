---
type: API
title: __mul64hi
description: 获取输入int64类型数据x和y乘积的高64位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mul64hi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __mul64hi

int64 高位乘法函数。获取输入 int64 类型数据 x 和 y 乘积的高 64 位。

函数原型：long long __mul64hi(long long x, long long y)

参数 x、y 为源操作数（乘数）。返回乘积的高 64 位。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [整型数学库函数](integer_math_functions.md)（`related`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；整型数学库函数正文界定“提供整型数据的位操作、乘法、绝对差与平均值等数学运算接口”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__mul_i32toi64](_mul_i32toi64.md)（`same_topic`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；__mul_i32toi64正文界定“计算输入32位整数x和y的乘积，返回64位结果”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__mulhi（整数数学函数）](_mulhi.md)（`same_topic`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；__mulhi（整数数学函数）正文界定“获取输入int32类型数据x和y乘积的高32位”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__umul64hi](_umul64hi.md)（`same_topic`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；__umul64hi正文界定“获取输入uint64类型数据x和y乘积的高64位”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__umulhi](_umulhi.md)（`same_topic`）：__umulhi：__mulhi与__umulhi只差有符号解释，64hi扩展相同高半乘积契约，__mul_i32toi64给出完整32位乘积以核对高位提取。 目标卡《__mul64hi》补充：获取输入int64类型数据x和y乘积的高64位。
<!-- cannbot:related:end -->
