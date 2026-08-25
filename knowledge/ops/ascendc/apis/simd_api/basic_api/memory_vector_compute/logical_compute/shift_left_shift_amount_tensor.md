---
type: API
title: ShiftLeft
description: 对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/ShiftLeft_shift_amount_tensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShiftLeft

对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。

本接口组包含 LocalTensor, LocalTensor。

本接口属于 UB 矢量计算逻辑运算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ShiftRight](shift_right_shift_amount_tensor.md)（`related`）：相同 tensor 位移量输入下，ShiftLeft 执行相反方向，可用于方向选择和 round-trip 位测试。
- [AscShiftLeft](../../../c_api/reg/logic_compute/asc_shiftleft.md)（`same_topic`）：ShiftLeft 与《AscShiftLeft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [AscShiftRight](../../../c_api/reg/logic_compute/asc_shiftright.md)（`same_topic`）：ShiftLeft 与《AscShiftRight》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [AscShiftleft](../../../c_api/vector_compute/asc_shiftleft.md)（`same_topic`）：ShiftLeft 与《AscShiftleft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [AscShiftright](../../../c_api/vector_compute/asc_shiftright.md)（`same_topic`）：ShiftLeft 与《AscShiftright》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [ShiftLeft](shift_left.md)（`same_topic`）：ShiftLeft 与《ShiftLeft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [ShiftLeft](../../reg_vector_compute/logical_compute/shift_left.md)（`same_topic`）：ShiftLeft 与《ShiftLeft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [ShiftLefts](../../reg_vector_compute/logical_compute/shift_lefts.md)（`same_topic`）：ShiftLeft 与《ShiftLefts》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
<!-- cannbot:related:end -->
