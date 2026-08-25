---
type: API
title: AscSubc
description: 根据mask对源操作数src0、src1及输入进位carry_src按元素求差，将结果写入dst，同时将进位结果写入carry寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_subc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSubc

该接口根据mask，对源操作数src0、src1及输入进位carry_src进行按元素求差操作，减法运算在硬件底层通过补码加法实现，将结果写入目的操作数dst，同时将每个元素的进位结果写入carry（存放进位的掩码寄存器）。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位，若src0，~src1，carry_src输入按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

以uint64_t类型数据计算0xFFFFFFFF FFFFFFFF - 0x00000000 00000008 = 0xFFFFFFFF FFFFFFF7为例，asc_sub/asc_subc接口的适用场景如下图

参数：carry(输出): 目的操作数（掩码寄存器）。存储补码加法计算后的进位数据。；dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；carry_src(输入): 源操作数（掩码寄存器），进位数据。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 运算输出完整计算结果（包含进位位），不受asc_set_ctrl影响，硬件不会对输出进行饱和或截断。

仅 Ascend 950PR/Ascend 950DT 支持。
