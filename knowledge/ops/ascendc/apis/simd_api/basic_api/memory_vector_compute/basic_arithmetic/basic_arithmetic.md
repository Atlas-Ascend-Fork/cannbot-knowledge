---
type: API
title: 基础算术
description: 矢量基础算术接口集，包含 Exp、Ln、Abs、Reciprocal、Add、Sub、Mul、Div 等单双目计算接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/basic_arithmetic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础算术

Memory 矢量基础算术接口集合，按操作类型分为：单目（Abs、Exp、Ln、Sqrt、Rsqrt、Reciprocal、Relu、Neg、LeakyRelu）、双目（Add、Sub、Mul、Div、Max、Min）、标量双目（Adds、Muls、Maxs、Mins、Subs、Divs，部分支持灵活标量位置）。ISASI 扩展含 BilinearInterpolation、Prelu、Mull。接口作用于 LocalTensor，需注意数据类型与 mask 配置。
