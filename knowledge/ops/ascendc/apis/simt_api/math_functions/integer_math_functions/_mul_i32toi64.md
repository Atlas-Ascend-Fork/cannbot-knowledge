---
type: API
title: __mul_i32toi64
description: 计算输入32位整数x和y的乘积，返回64位结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mul_i32toi64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __mul_i32toi64

32 位扩展为 64 位的乘法函数。计算输入 32 位整数 x 和 y 的乘积，返回 64 位结果。

函数原型（重载）：long long __mul_i32toi64(int x, int y)、unsigned long long __mul_i32toi64(unsigned int x, unsigned int y)

参数 x、y 为源操作数（乘数）。返回乘积的 64 位结果。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__mul24（整数数学函数）](_mul24.md)（`related`）：__mul_i32toi64 保留完整 32×32→64 位有符号乘积，而 __mul24 只使用低 24 位并返回低 32 位。
- [__mulhi（整数数学函数）](_mulhi.md)（`related`）：__mulhi 返回乘积高位，而 focal 返回完整 64 位结果；二者可按结果表示和指令成本选型。
- [__umulhi](_umulhi.md)（`related`）：__umulhi：__mulhi与__umulhi只差有符号解释，64hi扩展相同高半乘积契约，__mul_i32toi64给出完整32位乘积以核对高位提取。 目标卡《__mul_i32toi64》补充：计算输入32位整数x和y的乘积，返回64位结果。
- [__mul64hi](_mul64hi.md)（`same_topic`）：焦点处理整数乘积高半部的有符号/无符号与位宽变体；__mul_i32toi64正文界定“计算输入32位整数x和y的乘积，返回64位结果”。候选保持“乘积高半部”语义，只改变 32/64 位和有符号性。
<!-- cannbot:related:end -->
