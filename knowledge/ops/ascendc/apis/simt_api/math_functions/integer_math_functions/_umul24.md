---
type: API
title: __umul24
description: 获取uint32类型数据x和y的低24位乘积的低32位运算结果。x和y的高8位数据被忽略。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__umul24.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __umul24

24 位无符号乘法函数。获取 uint32 类型数据 x 和 y 低 24 位的乘积的低 32 位结果，x 和 y 的高 8 位被忽略。

函数原型：unsigned int __umul24(unsigned int x, unsigned int y)

参数 x、y 为源操作数。返回低 24 位乘积的低 32 位结果。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__mul24（整数数学函数）](_mul24.md)（`related`）：__umul24 是 __mul24 的无符号对应接口，两者都忽略输入高 8 位并返回低 32 位乘积。
- [__umulhi](_umulhi.md)（`related`）：__umulhi 返回完整 32×32 乘积的高 32 位，focal 返回低 24×24 乘积的低 32 位，二者输出部分不同。
<!-- cannbot:related:end -->
