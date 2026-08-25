---
type: API
title: AscAddc
description: 根据mask对源操作数src0、src1及输入进位carry_src按元素求和，将结果写入dst，同时将进位结果写入carry寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_addc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscAddc

该接口根据mask，对源操作数src0、src1及输入进位carry_src进行按元素求和操作，将结果写入目的操作数dst，同时将每个元素的进位结果写入carry（存放进位的掩码寄存器）。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位。若src0，src1，carry_src输入按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

以uint64_t类型数据计算0xFFFFFFFF FFFFFFFF + 0x00000000 00000008 = 0x00000000 00000007为例，asc_add/asc_addc接口的适用场景如下图

参数：carry(输出): 目的操作数（掩码寄存器）。存储加法计算后的进位数据。；dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；carry_src(输入): 源操作数（掩码寄存器），进位数据。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 运算输出完整计算结果（包含进位位），不受asc_set_ctrl影响，硬件不会对输出进行饱和或截断。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSubc](asc_subc.md)（`related`）：AscAddc 与 AscSubc 都显式消费和产生 carry mask，可组合实现多字宽加减。
- [AddC](../../../basic_api/reg_vector_compute/basic_arithmetic/add_c.md)（`same_topic`）：AddC 与《AscAddc》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [AscAdd](asc_add.md)（`same_topic`）：AscAdd 与《AscAddc》的实质衔接是：Reg、Vector 和 scalar 三种 AscAdd 入口实现相同加法，区别在操作数载体、mask 与结果位置。
- [SubC](../../../basic_api/reg_vector_compute/basic_arithmetic/sub_c.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；AscAddc正文说明“根据mask对源操作数src0、src1及输入进位carry_src按元素求和，将结果写入dst，同时将进位结果写入carry寄存器”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
<!-- cannbot:related:end -->
