---
type: API
title: 内置数据类型
description: SIMD与SIMT混合编程提供了一系列适用于Device侧的数据类型，包括标量、短向量和dim3结构体。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/builtin_data_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 内置数据类型

SIMD 与 SIMT 混合编程提供 Device 侧数据类型，包括标量、短向量和 dim3 结构体。

标量类型：bool（8bit）、整型（uint8_t/int8_t 到 uint64_t/int64_t）、浮点型（float8_e4m3_t、float8_e5m2_t、hifloat8_t、half、bfloat16_t、float）。浮点型按符号位/指数位/尾数位划分，如 half 为 1-5-10（16bit）、bfloat16_t 为 1-8-7（16bit）、float 为 1-8-23（32bit）。

短向量类型：固定长度向量（X2/X4），紧凑连续存储无填充，遵循自然对齐。支持 char/short/int/long/longlong 及对应 unsigned 类型的 uchar2/char4/short2/int4 等，以及 half2/bfloat16x2_t/float2/float4 等。通过 .x/.y/.z/.w 访问分量。提供 make_int2/make_float2 等构造函数（需包含 simt_api/vector_functions.h）。

dim3：内置结构体，由 3 个 unsigned int（x, y, z）组成，用于指定 Grid 和 Thread Block 维度，三维总数为 x * y * z。
