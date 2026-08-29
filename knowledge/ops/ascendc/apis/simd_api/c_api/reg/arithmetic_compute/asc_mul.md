---
type: API
title: AscMul
description: 根据mask对源操作数src0、src1按元素进行乘法运算，将结果写入目的操作数dst。仅在AIV上生效。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMul

该接口根据mask，对源操作数src0、src1按元素进行乘法运算，将结果写入目的操作数dst。

本接口仅在AIV上生效。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half。

约束：- 本接口在非AIV上调用直接返回。
- mask需通过掩码设置接口预先赋值后再传入，未赋值的掩码寄存器内容不确定，会导致有效元素位置错误。

仅 Ascend 950PR/Ascend 950DT 支持。
