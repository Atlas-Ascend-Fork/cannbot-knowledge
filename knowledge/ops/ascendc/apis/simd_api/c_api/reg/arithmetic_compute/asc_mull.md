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

- [基础算术](arithmetic_compute.md)（`related`）：《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscMull同时产生乘积高低位，只有同样保留溢出位的Mull接口可视为同一运算合同上存在可执行的直接衔接。
- [Mull](../../../basic_api/memory_vector_compute/basic_arithmetic/mull_isasi.md)（`same_topic`）：《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。；《Mull》说明双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。。二者在AscMull同时产生乘积高低位，只有同样保留溢出位的Mull接口可视为同一运算合同上存在可执行的直接衔接。
- [Mull](../../../basic_api/reg_vector_compute/basic_arithmetic/mull.md)（`same_topic`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
