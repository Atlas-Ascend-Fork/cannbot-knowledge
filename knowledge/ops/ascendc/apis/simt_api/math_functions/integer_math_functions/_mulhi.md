---
type: API
title: __mulhi（整数数学函数）
description: 获取输入int32类型数据x和y乘积的高32位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mulhi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __mulhi

int32 高位乘法函数。获取输入 int32 类型数据 x 和 y 乘积的高 32 位。

函数原型：int __mulhi(int x, int y)

参数 x、y 为源操作数（乘数）。返回乘积的高 32 位。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__mul24（整数数学函数）](_mul24.md)（`related`）：__mulhi 返回有符号整数乘积的高位，__mul24 返回低 24 位参与乘法后的低 32 位；二者用于不同的截位需求。
- [__mul_i32toi64](_mul_i32toi64.md)（`related`）：__mulhi 返回乘积高位，而 focal 返回完整 64 位结果；二者可按结果表示和指令成本选型。
- [__umulhi](_umulhi.md)（`related`）：__umulhi说明获取输入uint32类型数据x和y乘积的高32位；对__mulhi（整数数学函数）而言，__mulhi 与 __umulhi 都返回 32 位乘积的高 16 位，但有符号扩展不同，是整数溢出语义的直接选型点。
- [__mul64hi](_mul64hi.md)（`same_topic`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；__mulhi（整数数学函数）正文界定“获取输入int32类型数据x和y乘积的高32位”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
- [__umul64hi](_umul64hi.md)（`same_topic`）：__mulhi（整数数学函数）说明获取输入int32类型数据x和y乘积的高32位。
<!-- cannbot:related:end -->
