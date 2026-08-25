---
type: API
title: ShiftRight
description: 根据mask对srcReg0按srcReg1对应元素进行右移操作并写入dstReg，无符号类型执行逻辑右移，有符号类型执行算术右移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/ShiftRight.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ShiftRight

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"。

ShiftRight指令根据mask对源操作数srcReg0，按照srcReg1对应元素进行右移操作，将结果写入目的操作数dstReg。根据源操作数的数据类型，右移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑右移。

  逻辑右移会将二进制数整体向右移动指定的位数，每移动1位，最低位被丢弃，最高位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑右移1位后，结果为0101010101010101。
- 数据类型为有符号类型：执行算术右移。

  算术右移会将二进制数整体向右移动指定的位数，每移动1位，最低位被丢弃，最高位复制符号位。例如，二进制数1010101010101010（int16_t类型）算术右移1位后，结果为1101010101010101；算术右移3位后，结果为1111010101010101。

参数：T: 源操作数数据类型。；U: 右移参数数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；V: 右移参数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。；srcReg1(输入): 源操作数。 类型为RegTensor。 不支持设置为负数，负数行为未定义。

约束：- 对于逻辑位移（无符号数据类型），如果位移量（srcReg1）大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果srcReg0小于0，位移量大于数据类型位宽，则输出-1；如果srcReg0大于0，位移量大于数据类型位宽，则输出0。
- srcReg1不支持设置为负数，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ShiftRight](../../memory_vector_compute/logical_compute/shift_right.md)（`related`）：Memory ShiftRight 用单个 scalarValue 并可舍入，Reg ShiftRight 用 srcReg1 逐 lane 指定位移；两者共享有符号算术/无符号逻辑右移和超位宽边界。
- [AscShiftright](../../../c_api/vector_compute/asc_shiftright.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRight》补充：根据mask对srcReg0按srcReg1对应元素进行右移操作并写入dstReg，无符号类型执行逻辑右移，有符号类型执行算术右移。
- [ShiftRight](../../memory_vector_compute/logical_compute/shift_right_shift_amount_tensor.md)（`same_topic`）：RegTensor 版本完成相同逐元素右移，可按数据驻留位置选择。
<!-- cannbot:related:end -->
