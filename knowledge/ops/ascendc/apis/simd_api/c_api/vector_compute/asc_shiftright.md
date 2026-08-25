---
type: API
title: AscShiftright
description: 对src中的每个元素执行右移，右移大小为value。 - 对于int16_t/int32_t，做算术右移（去掉最低位，最高位复制符号位）。
  - 对于uint16_t/uint32_t，做逻辑右移（去掉最低位，最高位填充为0）。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_shiftright.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscShiftright

对src中的每个元素执行右移，右移大小为value。
函数原型：void asc_shiftright(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, int32_t value, uint32_t count)
约束：value不支持设置为负数。；value取值不能超过src数据类型的位宽。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscShiftRight](../reg/logic_compute/asc_shiftright.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《AscShiftRight》补充：根据mask对输入数据src0按照src1对应元素进行右移操作，结果写入dst。
- [AscShiftRightScalar](../reg/logic_compute/asc_shiftright_scalar.md)（`same_topic`）：AscShiftRightScalar 与 AscShiftright 都用一个标量位数右移向量元素，并按有符号/无符号选择算术或逻辑右移；执行载体和越界约束不同。
- [ShiftLeft](../../basic_api/memory_vector_compute/logical_compute/shift_left_shift_amount_tensor.md)（`same_topic`）：ShiftLeft 与《AscShiftright》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
- [ShiftRight](../../basic_api/memory_vector_compute/logical_compute/shift_right.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRight》补充：对源操作数中的每个元素进行右移操作，右移位数由标量scalarValue决定，无符号类型执行逻辑右移，有符号类型执行算术右移，支持舍入功能。
- [ShiftRight](../../basic_api/memory_vector_compute/logical_compute/shift_right_shift_amount_tensor.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRight》补充：对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。
- [ShiftRight](../../basic_api/reg_vector_compute/logical_compute/shift_right.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRight》补充：根据mask对srcReg0按srcReg1对应元素进行右移操作并写入dstReg，无符号类型执行逻辑右移，有符号类型执行算术右移。
- [ShiftRights](../../basic_api/reg_vector_compute/logical_compute/shift_rights.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRights》补充：根据mask对srcReg按标量scalarValue进行右移操作并写入dstReg，无符号类型执行逻辑右移，有符号类型执行算术右移。
<!-- cannbot:related:end -->
