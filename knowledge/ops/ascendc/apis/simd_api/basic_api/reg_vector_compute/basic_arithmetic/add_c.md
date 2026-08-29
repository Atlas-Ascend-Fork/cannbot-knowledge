---
type: API
title: AddC
description: 对srcReg0、srcReg1及输入进位按元素求和，结果写入dstReg和carry。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/AddC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AddC

对srcReg0、srcReg1及输入进位按元素求和，结果写入dstReg和carry。

头文件引用路径为"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。 MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为 RegTensor 的八分之一（VL/8）。如下图所示，当操作数类型为b8时，每一个element对应1bit MaskReg；当操作数类型为b16时，每一个element对应2bit MaskReg，且仅2bit中的最低位是有效的；当操作数类型为b32时，每一个element对应4bit MaskReg，且仅4bit中的最低位是有效的。 图1 MaskReg计算过程

本接口组包含 MaskReg, RegTensor, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8/b16/b32/b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

返回值：MaskReg

约束：MaskReg寄存器数量上限为8。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscAddc](../../../c_api/reg/arithmetic_compute/asc_addc.md)（`same_topic`）：对srcReg0、srcReg1及输入进位按元素求和，结果写入dstReg和carry；该接口根据mask，对源操作数src0、src1及输入进位carry_src进行按元素求和操作，将结果写入目的操作数dst，同时将每个元素的进位结果写入carry（存放进位的掩码寄存器）。两卡描述同一带输入进位的寄存器逐元素加法；候选补充 uint32_t、mask 置零和完整进位输出合同。
<!-- cannbot:related:end -->
