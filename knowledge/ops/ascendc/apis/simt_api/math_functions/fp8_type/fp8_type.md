---
type: API
title: fp8类型
description: 介绍FP8数据类型（e4m3、e5m2、hifloat8）并提供相关数据转换函数的入口。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_type.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# fp8类型

SIMT 编程支持三种 FP8 数据类型：float8_e4m3_t（1 位符号、4 位指数、3 位尾数）、float8_e5m2_t（1 位符号、5 位指数、2 位尾数）和 hifloat8_t（指数与尾数位宽由点域编码字段 D 决定）。三者均占用 8 位，面向低精度训练与推理场景。
本入口包含两部分导航：fp8 数据类型简介说明各类型的位宽分布与取值范围；fp8 数据转换函数提供与 half、float 等高精度类型之间的相互转换接口。
使用 FP8 接口前需确认目标硬件支持 FP8 计算，并按算子语义选择合适的编码格式。

<!-- cannbot:related:start -->
## 相关

- [__e5m2x22float2](fp8_conversion_functions/_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《fp8类型》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
