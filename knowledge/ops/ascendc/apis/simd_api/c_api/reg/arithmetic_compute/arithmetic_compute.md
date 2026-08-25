---
type: API
title: 基础算术
description: 寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/arithmetic_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础算术

寄存器侧基础算术接口提供逐元素矢量运算。四则运算含asc_add/sub/mul/div及asc_add_scalar/mul_scalar/max_scalar/min_scalar标量变体，asc_addc/subc支持常量加减。
数学函数含asc_exp/ln/sqrt及asc_abs/neg。激活函数含asc_relu/leakyrelu/prelu。比较运算含asc_max/min及标量变体，asc_mull提供长乘。asc_muls已废弃，建议使用asc_mul_scalar替代。
