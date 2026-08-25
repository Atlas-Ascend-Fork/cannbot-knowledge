---
type: API
title: Sub
description: 根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Sub

该接口根据mask，对源操作数srcReg0、srcReg1进行按元素求差操作，将结果写入目的操作数dstReg。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位。减法运算在硬件底层通过补码加法实现，该接口可以在carry（MaskReg寄存器）中标记每次补码加法是否产生进位，若srcReg0，~srcReg1，33'b1，按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

计算结果不保留进位，计算结果保留进位，输出carry适用场景

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。；srcReg1(输入): 源操作数。 类型为RegTensor。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。；carry(输出): 目的操作数。输出进位值。类型为MaskReg。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《Sub》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [AddC](add_c.md)（`related`）：AddC 与《Sub》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [Sub](../../memory_vector_compute/basic_arithmetic/sub.md)（`related`）：The Reg-vector Sub performs the same elementwise subtraction in register programming, enabling an execution-model choice against Memory-vector Sub.
- [AscSub](../../../c_api/reg/arithmetic_compute/asc_sub.md)（`same_topic`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Sub》说明根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSub](../../../c_api/vector_compute/asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Sub》补充：根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。
- [SubC](sub_c.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；Sub正文说明“根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
<!-- cannbot:related:end -->
