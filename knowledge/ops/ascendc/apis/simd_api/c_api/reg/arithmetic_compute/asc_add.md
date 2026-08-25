---
type: API
title: AscAdd
description: 根据mask对源操作数src0、src1按元素求和，将结果写入目的操作数dst。可选保留进位到carry寄存器。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscAdd

该接口根据mask，对源操作数src0、src1进行按元素求和操作，将结果写入目的操作数dst。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位。该接口可以在carry（掩码寄存器）中标记每次加法是否产生进位，若src0，src1输入按位相加后最高位有进位，在carry中对应位置每4bit的最低位写1，否则写0。

计算结果不保留进位，计算结果保留进位，输出carry适用场景

参数：carry(输出): 目的操作数（掩码寄存器）。用来存储加法计算后的进位数据。；dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 支持进位计算接口
  - 仅支持uint32_t类型。
  - 需手动调用，接口内部不支持自动识别触发。
  - 运算输出完整计算结果（包含进位位），不受asc_set_ctrl影响，硬件不会对输出进行饱和或截断。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Add算子快速入门](../../../../../guides/getting_started/quick_start/simd_programming/add_op_quick_start.md)（`explains`）：在 950 的 C Reg 路径中 AscAdd 以 RegTensor+mask 实现同一 z=x+y，可作为快速入门 C 计算步骤在寄存器编程模式下的对应入口。
- [AddC](../../../basic_api/reg_vector_compute/basic_arithmetic/add_c.md)（`related`）：AddC 与《AscAdd》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [AscAdd](../../vector_compute/asc_add.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAdd》补充：根据mask对源操作数src0、src1按元素求和，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscAddScalar](asc_add_scalar.md)（`same_topic`）：AscAdd 与《AscAddScalar》的实质衔接是：Reg、Vector 和 scalar 三种 AscAdd 入口实现相同加法，区别在操作数载体、mask 与结果位置。
- [AscAddScalar](../../vector_compute/asc_add_scalar.md)（`same_topic`）：AscAdd说明根据mask对源操作数src0、src1按元素求和，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscAddc](asc_addc.md)（`same_topic`）：AscAdd 与《AscAddc》的实质衔接是：Reg、Vector 和 scalar 三种 AscAdd 入口实现相同加法，区别在操作数载体、mask 与结果位置。
<!-- cannbot:related:end -->
