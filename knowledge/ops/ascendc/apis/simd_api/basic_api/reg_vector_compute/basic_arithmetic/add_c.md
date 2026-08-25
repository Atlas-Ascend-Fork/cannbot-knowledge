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

- [Add](add.md)（`related`）：AddC 与《Add》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [AscAdd](../../../c_api/reg/arithmetic_compute/asc_add.md)（`related`）：AddC 与《AscAdd》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [Sub](sub.md)（`related`）：AddC 与《Sub》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [AscAddc](../../../c_api/reg/arithmetic_compute/asc_addc.md)（`same_topic`）：AddC 与《AscAddc》的实质衔接是：AddC 在逐 lane 加法中消费输入 carry 并产生输出 carry；Add/SubC 与 AscAddc/AscAdd 用同一 carry 寄存器契约界定普通加法和带进位运算的差别。
- [SubC](sub_c.md)（`same_topic`）：焦点处理SubC 的带借位减法、carry 输入输出和对应加法；AddC正文说明“对srcReg0、srcReg1及输入进位按元素求和，结果写入dstReg和carry”。候选与 SubC 共享 carry 寄存器契约，分别覆盖普通减法、带借位减法和带进位加法。
<!-- cannbot:related:end -->
