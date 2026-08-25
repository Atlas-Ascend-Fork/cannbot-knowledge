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

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Vector Sub 源 UB 非 32B 对齐触发错误 340》说明Ascend950/arch35 上用 AscendC::Sub Level 2 接口对 LocalTensor 做相邻元素差分时，若某个源是 LocalTensor::operator[] 的非零偏移切片（如 rpLocal[1]，偏移 1×sizeof(int32_t)=4 字节），起始地址不满足 Vector 指令 32B 对齐要求，运行时触发错误码 507035、plog 报 errcode:(340) The instruction access UB address is not aligned。判别=grep plog 取 errcode + 审查 Sub/Subs/Add 调用源是否为 operator[] 非零偏移切片 + 临时注释可疑 Sub 验证错误消失。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSubRelu](../../vector_compute/asc_sub_relu.md)（`related`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《AscSubRelu》说明按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [基础算术](arithmetic_compute.md)（`related`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《基础算术》说明寄存器侧基础算术类接口汇总，提供abs、add、sub、mul、div、exp、ln、sqrt、relu等逐元素矢量计算能力。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSub](../../vector_compute/asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSub》补充：根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscSubScalar](../../vector_compute/asc_sub_scalar.md)（`same_topic`）：AscSub说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscSubc](asc_subc.md)（`same_topic`）：AscSub 不接收输入 carry，而 AscSubc 接收 carry_src 并输出 carry，按是否需要多字宽借位链选型。
- [Sub](../../../basic_api/memory_vector_compute/basic_arithmetic/sub.md)（`same_topic`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Sub》说明双目矢量计算接口，对两个输入tensor按元素求差。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [Sub](../../../basic_api/reg_vector_compute/basic_arithmetic/sub.md)（`same_topic`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Sub》说明根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
