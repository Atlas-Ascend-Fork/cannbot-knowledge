---
type: API
title: __mul24（整数数学函数）
description: 获取int32类型数据x和y的低24位乘积的低32位运算结果。x和y的高8位数据被忽略。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mul24.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __mul24

24 位有符号乘法函数。获取 int32 类型数据 x 和 y 低 24 位的乘积的低 32 位结果，x 和 y 的高 8 位被忽略。

函数原型：int __mul24(int x, int y)

参数 x、y 为源操作数。返回低 24 位乘积的低 32 位结果。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__mul_i32toi64](_mul_i32toi64.md)（`related`）：__mul_i32toi64 保留完整 32×32→64 位有符号乘积，而 __mul24 只使用低 24 位并返回低 32 位。
- [__mulhi（整数数学函数）](_mulhi.md)（`related`）：__mulhi 返回有符号整数乘积的高位，__mul24 返回低 24 位参与乘法后的低 32 位；二者用于不同的截位需求。
- [__umul24](_umul24.md)（`related`）：__umul24 是 __mul24 的无符号对应接口，两者都忽略输入高 8 位并返回低 32 位乘积。
<!-- cannbot:related:end -->
