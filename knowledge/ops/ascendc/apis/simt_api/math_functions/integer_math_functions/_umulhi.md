---
type: API
title: __umulhi
description: 获取输入uint32类型数据x和y乘积的高32位。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__umulhi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __umulhi

uint32 高位乘法函数。获取输入 uint32 类型数据 x 和 y 乘积的高 32 位。

函数原型：unsigned int __umulhi(unsigned int x, unsigned int y)

参数 x、y 为源操作数（乘数）。返回乘积的高 32 位。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__mul_i32toi64](_mul_i32toi64.md)（`related`）：__umulhi：__mulhi与__umulhi只差有符号解释，64hi扩展相同高半乘积契约，__mul_i32toi64给出完整32位乘积以核对高位提取。 目标卡《__mul_i32toi64》补充：计算输入32位整数x和y的乘积，返回64位结果。
- [__mulhi（整数数学函数）](_mulhi.md)（`related`）：__umulhi说明获取输入uint32类型数据x和y乘积的高32位；对__mulhi（整数数学函数）而言，__mulhi 与 __umulhi 都返回 32 位乘积的高 16 位，但有符号扩展不同，是整数溢出语义的直接选型点。
- [__umul24](_umul24.md)（`related`）：__umulhi 返回完整 32×32 乘积的高 32 位，focal 返回低 24×24 乘积的低 32 位，二者输出部分不同。
- [__mul64hi](_mul64hi.md)（`same_topic`）：__umulhi：__mulhi与__umulhi只差有符号解释，64hi扩展相同高半乘积契约，__mul_i32toi64给出完整32位乘积以核对高位提取。 目标卡《__mul64hi》补充：获取输入int64类型数据x和y乘积的高64位。
- [__umul64hi](_umul64hi.md)（`same_topic`）：__umulhi：__mulhi与__umulhi只差有符号解释，64hi扩展相同高半乘积契约，__mul_i32toi64给出完整32位乘积以核对高位提取。 目标卡《__umul64hi》补充：获取输入uint64类型数据x和y乘积的高64位。
<!-- cannbot:related:end -->
