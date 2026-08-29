---
type: API
title: AscMull
description: 根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_mull.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscMull

该接口根据mask对输入数据src0、src1执行按元素相乘操作，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。计算公式及图示

参数：dst0(输出): 目的操作数（矢量数据寄存器）。；dst1(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int32_t、uint32_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Mull](../../../basic_api/reg_vector_compute/basic_arithmetic/mull.md)（`same_topic`）：该接口根据mask对输入数据src0、src1执行按元素相乘操作，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。；该接口根据mask对输入数据srcReg0、srcReg1按元素相乘操作，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。。两端实现完全相同的带 mask 整数宽乘结果拆分，差别是 C API 矢量寄存器与基础 RegTensor API 表面，互读可完成接口层选型。
<!-- cannbot:related:end -->
