---
type: API
title: AscMadd
description: 完成dst与src0逐元素相乘再加src1的融合乘加运算，根据mask将结果写回dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compound_compute/asc_madd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscMadd

madd（multiply-add），该接口用于完成dst与src0逐元素相乘再加src1的融合乘加运算，根据mask将计算结果写回dst。

参数：dst(输入/输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。
