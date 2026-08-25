---
type: API
title: 复合计算
description: 寄存器侧复合计算类接口汇总，提供abs_sub、axpy、madd、fma等多操作融合的矢量计算能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compound_compute/compound_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 复合计算

寄存器侧复合计算接口提供多操作融合的矢量运算，减少中间数据搬运和指令开销。asc_fma执行融合乘加（a*b+c），asc_madd执行乘加，asc_axpy执行标量乘加（a*x+y）。
asc_abs_sub计算绝对值差。asc_exp_sub已废弃。
