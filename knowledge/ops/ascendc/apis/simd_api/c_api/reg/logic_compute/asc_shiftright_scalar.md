---
type: API
title: AscShiftRightScalar
description: 根据mask对源操作数src执行右移，右移位数由标量参数value决定，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_shiftright_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscShiftRightScalar

根据mask对源操作数src执行右移，右移的位数由输入参数value决定，将结果写入目的操作数dst。根据源操作数的数据类型，右移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑右移。

逻辑右移会将二进制数整体向右移动指定的位数，最低位被丢弃，最高位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑右移1位后，结果为0101010101010101。
- 数据类型为有符号类型：执行算术右移。

算术右移会将二进制数整体向右移动指定的位数，最低位被丢弃，最高位复制符号位。例如，二进制数1010101010101010（int16_t类型）算术右移1位后，结果为1101010101010101；算术右移3位后，结果为1111010101010101。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。不支持设置为负数。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 对于逻辑位移（无符号数据类型），如果位移量大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果src小于0，位移量大于数据类型位宽，则输出-1；如果src大于0，位移量大于数据类型位宽，则输出0。
- value不支持设置为负数，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscShiftLeftScalar](asc_shiftleft_scalar.md)（`related`）：对应的标量左移用于相反方向的位运算，迁移时需显式区分符号与方向。
- [AscShiftRight](asc_shiftright.md)（`same_topic`）：asc_shiftright 使用寄存器位移量，而 scalar 版本使用统一标量；两者按位移量来源选型。
- [AscShiftright](../../vector_compute/asc_shiftright.md)（`same_topic`）：AscShiftRightScalar 与 AscShiftright 都用一个标量位数右移向量元素，并按有符号/无符号选择算术或逻辑右移；执行载体和越界约束不同。
- [ShiftRights](../../../basic_api/reg_vector_compute/logical_compute/shift_rights.md)（`same_topic`）：C++ Reg ShiftRights 与 C API AscShiftRightScalar 共享标量右移语义，可用于语言接口映射。
<!-- cannbot:related:end -->
