---
type: API
title: ShiftLefts
description: 根据mask对srcReg按标量scalarValue进行左移操作并写入dstReg，无符号类型执行逻辑左移，有符号类型执行算术左移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/ShiftLefts.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ShiftLefts

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_binary_scalar_intf.h"。

ShiftLefts指令根据mask对源操作数srcReg，按照scalarValue进行左移操作，将结果写入目的操作数dstReg。根据源操作数的数据类型，左移操作分为以下两种情况
- 数据类型为无符号类型：执行逻辑左移。

  逻辑左移会将二进制数整体向左移动指定的位数，每移动1位，最高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（uint16_t类型）逻辑左移1位后，结果为0101010101010100。
- 数据类型为有符号类型：执行算术左移。

  算术左移会将二进制数整体向左移动指定的位数，每移动1位，符号位保留，次高位被丢弃，最低位用0填充。例如，二进制数1010101010101010（int16_t类型）算术左移1位后，结果为1101010101010100；算术左移3位后，结果为1101010101010000。

参数：T: 矢量目的操作数和源操作数的数据类型。；U: 标量源操作数的数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；S: 矢量目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。 数据类型需要与目的操作数保持一致。；scalarValue(输入): 左移的位数。 类型为一个标量。 不支持设置为负数，负数行为未定义。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：- 对于逻辑位移（无符号数据类型），如果位移量（scalarValue）大于数据类型位宽，则输出为0。
- 对于算术位移（有符号数据类型），如果位移量大于数据类型位宽，则输出0。
- scalarValue不支持设置为负数，负数行为未定义。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ShiftLeft](shift_left.md)（`same_topic`）：“ShiftLefts指令根据mask对源操作数srcReg，按照scalarValue进行左移操作，将结果写入目的操作数dstReg。”与“ShiftLeft指令根据mask对源操作数srcReg0，按照srcReg1对应元素进行左移操作，将结果写入目的操作数dstReg。”提供双方正文证据。二者定义同一掩码寄存器左移操作，差异只在移位量由单个 scalarValue 还是逐元素 srcReg1 提供，互读可直接选择标量或向量移位版本。
<!-- cannbot:related:end -->
