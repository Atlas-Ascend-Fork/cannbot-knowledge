---
type: API
title: 基础算术
description: Reg矢量计算基础算术接口索引页，涵盖Abs、Exp、Sqrt、Ln、Log、Add、Sub、Mul、Max、Min及Relu/LeakyRelu等。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/basic_arithmetic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础算术

Reg 矢量基础算术接口集合，作用于寄存器侧 Tensor。单目含 Abs、Exp、Sqrt、Ln、Log、Log2、Log10、Neg、Relu、Prelu、LeakyRelu；双目含 Add、Sub、Mul、Mull、Div、Max、Min，AddC/SubC 为带常量版本；标量双目含 Adds、Muls、Maxs、Mins。相比 Memory 版本，Reg 版本直接操作寄存器，延迟更低但需配合 Load/Store 使用。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算概述](overview.md)（`same_topic`）：Reg 基础算术索引逐项列出加减乘除、指数和复合运算，是 Overview 所概括能力的直接 API 导航。
<!-- cannbot:related:end -->
