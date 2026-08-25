---
type: API
title: AscGe
description: 逐元素比较两个源操作数是否大于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_ge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscGe

ge（greater than or equal to），该接口用于逐元素比较两个源操作数大小，将比较结果（）写入目的操作数dst对应比特位，如果比较结果为真，则对应比特位为1，否则为0。

参数：dst(输出): 目的操作数（掩码寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 通过mask参数控制的未选中元素在目的操作数中被置零。
- 操作数重叠约束：src0和src1可以是同一个矢量数据寄存器。
- 浮点数据类型比较，涉及nan时比较结果为0。
- 当源操作数为浮点数据类型时，+0与-0视为相等。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](asc_select.md)（`related`）：AscSelect 消费 AscGe 等比较接口生成的 mask，在两个源寄存器之间逐 lane 选值。
- [Compare](../../../basic_api/reg_vector_compute/compare_and_select/compare.md)（`related`）：Reg 基础 API Compare 以比较模式选择 GE 等谓词，是 AscGe C API 在 C++ Reg 层的对应能力。
- [比较与选择](../../../basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`related`）：Reg 比较与选择入口把 AscGe 所属的比较结果生成和后续 Select/Squeeze 消费放在同一工作流中。
- [比较与选择概述](../../../basic_api/reg_vector_compute/compare_and_select/overview.md)（`related`）：Reg 比较概述解释比较结果如何进入 MaskReg 并驱动选择，是理解 AscGe 输出用途的机制背景。
- [AscGe](../../vector_compute/asc_ge.md)（`same_topic`）：《AscGe》明确“逐元素比较两个源操作数是否大于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0。”；它与《AscGe》的“Ge（greater than or equal to），逐元素比较src0 >= src1是否成立，成立则输出结果为1，否则输出结果为0，每个元素的比较结果占一个bit。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscGeScalar](asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscGe正文界定“逐元素比较两个源操作数是否大于等于，比较结果写入目的操作数对应比特位，为真则置1，否则置0”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
<!-- cannbot:related:end -->
