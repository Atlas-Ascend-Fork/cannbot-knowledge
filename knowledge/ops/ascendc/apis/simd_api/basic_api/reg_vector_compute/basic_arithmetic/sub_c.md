---
type: API
title: SubC
description: 根据mask对源操作数srcReg0、srcReg1及输入进位carrySrc按元素求差，将结果写入dstReg，同时将进位结果写入carry寄存器。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/SubC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# SubC

该接口根据mask，对源操作数srcReg0、srcReg1及输入进位carrySrc进行按元素求差操作，减法运算在硬件底层通过补码加法实现，将结果写入目的操作数dstReg，同时将每个元素的进位结果写入carry（存放进位的MaskReg寄存器）。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位，若srcReg0，~srcReg1，carrySrc输入按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

以int64_t类型数据计算-1 - 8 = -9为例，Sub/SubC接口的适用场景如下图

头文件："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；carry(输出): 目的操作数。输出进位值。 类型为MaskReg。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。；srcReg1(输入): 源操作数。 类型为RegTensor。；carrySrc(输入): 源操作数。输入进位值。 类型为MaskReg。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：int32_t、uint32_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Add](add.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；Add正文说明“对srcReg0和srcReg1按元素求和，结果写入dstReg，可选保留进位”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
- [AddC](add_c.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；AddC正文说明“对srcReg0、srcReg1及输入进位按元素求和，结果写入dstReg和carry”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
- [AscAddc](../../../c_api/reg/arithmetic_compute/asc_addc.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；AscAddc正文说明“根据mask对源操作数src0、src1及输入进位carry_src按元素求和，将结果写入dst，同时将进位结果写入carry寄存器”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
- [AscSubc](../../../c_api/reg/arithmetic_compute/asc_subc.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；AscSubc正文说明“根据mask对源操作数src0、src1及输入进位carry_src按元素求差，将结果写入dst，同时将进位结果写入carry寄存器”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
- [Sub](sub.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；Sub正文说明“根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
<!-- cannbot:related:end -->
