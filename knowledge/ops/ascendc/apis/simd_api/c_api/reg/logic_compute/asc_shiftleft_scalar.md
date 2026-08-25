---
type: API
title: AscShiftLeftScalar
description: 根据mask对源操作数src执行左移，左移位数由标量参数value决定，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_shiftleft_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscShiftLeftScalar

根据mask对源操作数src执行左移，左移的位数由输入参数value决定，将结果写入目的操作数dst。根据源操作数的数据类型，左移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑左移。

逻辑左移会将二进制数整体向左移动指定的位数，最高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑左移1位后，结果为0101010101010100。
- 数据类型为有符号类型：执行算术左移。

算术左移会将二进制数整体向左移动指定的位数，次高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（int16_t类型）算术左移1位后，结果为1101010101010100；算术左移3位后，结果为1101010101010000。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。不支持设置为负数。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 对于逻辑位移（无符号数据类型），如果位移量（value）大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果位移量（value）大于数据类型位宽，则输出为0。
- value不支持设置为负，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscShiftRightScalar](asc_shiftright_scalar.md)（`related`）：对应的标量左移用于相反方向的位运算，迁移时需显式区分符号与方向。
- [AscShiftLeft](asc_shiftleft.md)（`same_topic`）：AscShiftLeftScalar 与《AscShiftLeft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [AscShiftleft](../../vector_compute/asc_shiftleft.md)（`same_topic`）：AscShiftLeftScalar 与《AscShiftleft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [ShiftLeft](../../../basic_api/memory_vector_compute/logical_compute/shift_left.md)（`same_topic`）：AscShiftLeftScalar 与《ShiftLeft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [ShiftLeft](../../../basic_api/reg_vector_compute/logical_compute/shift_left.md)（`same_topic`）：AscShiftLeftScalar 与《ShiftLeft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [ShiftLefts](../../../basic_api/reg_vector_compute/logical_compute/shift_lefts.md)（`same_topic`）：《AscShiftLeftScalar》明确“根据mask对源操作数src执行左移，左移位数由标量参数value决定，结果写入dst。”；它与《ShiftLefts》的“根据mask对srcReg按标量scalarValue进行左移操作并写入dstReg，无符号类型执行逻辑左移，有符号类型执行算术左移。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
