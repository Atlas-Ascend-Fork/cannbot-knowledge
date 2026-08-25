---
type: API
title: 数学计算
description: AscendC SIMD高级数学计算接口导航页，涵盖三角函数、指数对数、取整、逻辑运算等按元素计算接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/math_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 数学计算

Ascend C SIMD 高阶 API 数学计算导航页，提供按元素（element-wise）数学运算的 Kernel 侧接口。
涵盖三角函数（Sin、Cos、Tan、Asin、Acos、Atan 及双曲变体）、指数对数（Exp、Log、Lgamma、Digamma）、取整截断（Floor、Ceil、Round、Trunc、Frac）、误差函数（Erf、Erfc）及符号判断（Sign）等。
另包含逻辑运算（LogicalAnd/Or/Xor/Not 及变体）、位运算（BitwiseAnd/Or/Xor/Not）、数值检查（IsNan、IsInf、IsFinite）、融合运算（Fma、Axpy、Hypot）及条件选择（Where）等接口。
各接口通常配合对应的 Tiling 临时空间查询方法使用。
