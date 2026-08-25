---
type: API
title: 扩展语法内置宏
description: 下表列出了一些常用的内置宏，涵盖了bfloat16、half和float三种浮点类型的特殊值，以及常用的数学常数、对数和边界值。当开发者需要处理浮点边界或数学常量时，可以直接参考并使用这些内置宏，无需手动定义或查阅具体的数值，从而可以将更多精力集中在算法逻辑上。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/builtin_macros.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 扩展语法内置宏

提供常用内置宏，涵盖 bfloat16、half 和 float 三种浮点类型的特殊值及常用数学常数。开发者可直接使用，无需手动定义。

bfloat16 特殊值宏（需 asc_bf16.h）：ASCRT_INF_BF16、ASCRT_MAX_NORMAL_BF16、ASCRT_MIN_DENORM_BF16、ASCRT_NAN_BF16、ASCRT_NEG_ZERO_BF16、ASCRT_ONE_BF16、ASCRT_ZERO_BF16。

half 特殊值宏（需 asc_fp16.h）：ASCRT_INF_FP16、ASCRT_MAX_NORMAL_FP16、ASCRT_MIN_DENORM_FP16、ASCRT_NAN_FP16、ASCRT_NEG_ZERO_FP16、ASCRT_ONE_FP16、ASCRT_ZERO_FP16。

float 特殊值与数学常数宏（需 math_constants.h）：ASCRT_INF_F、ASCRT_NAN_F、ASCRT_MAX_NORMAL_F、ASCRT_PI_F、ASCRT_SQRT_HALF_F、ASCRT_LN2_F、ASCRT_L2E_F 等，涵盖特殊值、圆周率、对数、平方根、幂值等常用数学常量。还包含 ASCRT_MIN_VAL_S/ASCRT_MAX_VAL_S（int32 最小/最大值）。
