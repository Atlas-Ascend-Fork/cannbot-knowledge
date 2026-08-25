---
type: API
title: AscShiftLeft
description: 根据mask对输入数据src0按照src1对应元素进行左移操作，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_shiftleft.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscShiftLeft

根据掩码mask对输入数据src0，按照src1对应元素进行左移操作，完成后将结果写入dst中。根据源操作数的数据类型，左移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑左移。

逻辑左移会将二进制数整体向左移动指定的位数，最高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑左移1位后，结果为0101010101010100。
- 数据类型为有符号类型：执行算术左移。

算术左移会将二进制数整体向左移动指定的位数，次高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（int16_t类型）算术左移1位后，结果为1101010101010100；算术左移3位后，结果为1101010101010000。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 对于逻辑位移（无符号数据类型），如果位移量大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果位移量大于数据类型位宽，则输出为0。
- src1内元素不支持设置为负数，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscShiftLeftScalar](asc_shiftleft_scalar.md)（`same_topic`）：AscShiftLeftScalar 与《AscShiftLeft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [AscShiftleft](../../vector_compute/asc_shiftleft.md)（`same_topic`）：AscShiftLeft说明根据mask对输入数据src0按照src1对应元素进行左移操作，结果写入dst。
- [ShiftLeft](../../../basic_api/memory_vector_compute/logical_compute/shift_left.md)（`same_topic`）：ShiftLeft说明对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。
- [ShiftLeft](../../../basic_api/memory_vector_compute/logical_compute/shift_left_shift_amount_tensor.md)（`same_topic`）：ShiftLeft 与《AscShiftLeft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [ShiftLeft](../../../basic_api/reg_vector_compute/logical_compute/shift_left.md)（`same_topic`）：ShiftLeft说明根据mask对srcReg0按srcReg1对应元素进行左移操作并写入dstReg，无符号类型执行逻辑左移，有符号类型执行算术左移。
<!-- cannbot:related:end -->
