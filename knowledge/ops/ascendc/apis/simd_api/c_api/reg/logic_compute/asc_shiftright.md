---
type: API
title: AscShiftRight
description: 根据mask对输入数据src0按照src1对应元素进行右移操作，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/logic_compute/asc_shiftright.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscShiftRight

根据掩码mask对输入数据src0，按照src1对应元素进行右移操作，完成后将结果写入dst中。根据源操作数的数据类型，右移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑右移。

逻辑右移会将二进制数整体向右移动指定的位数，最低位被丢弃，最高位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑右移1位后，结果为0101010101010101。
- 数据类型为有符号类型：执行算术右移。

算术右移会将二进制数整体向右移动指定的位数，最低位被丢弃，最高位复制符号位。例如，二进制数1010101010101010（int16_t类型）算术右移1位后，结果为1101010101010101；算术右移3位后，结果为1111010101010101。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- 对于逻辑位移（无符号数据类型），如果位移量大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果src0小于0，位移量大于数据类型位宽，则输出-1；如果src0大于0，位移量大于数据类型位宽，则输出0。
- src1不支持设置为负数，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。
