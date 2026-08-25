---
type: API
title: AscSub
description: 根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscSub

该接口根据mask，对源操作数src0、src1进行按元素求差操作，将结果写入目的操作数dst。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位。减法运算在硬件底层通过补码加法实现，该接口可以在carry（掩码寄存器）中标记每次补码加法是否产生进位，若src0，~src1，33'b1，按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

计算结果不保留进位，计算结果保留进位，输出carry适用场景

参数：carry(输出): 目的操作数（掩码寄存器）。用来存储补码加法计算后的进位数据。；dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 支持进位计算接口
  - 仅支持uint32_t类型。
  - 需手动调用，接口内部不支持自动识别触发。
  - 运算输出完整计算结果（包含进位位），不受asc_set_ctrl影响，硬件不会对输出进行饱和或截断。

仅 Ascend 950PR/Ascend 950DT 支持。
