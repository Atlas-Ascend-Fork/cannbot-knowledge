---
type: API
title: AscShiftleft
description: 将所有元素左移distance位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_shiftleft.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscShiftleft

将所有元素左移distance位。计算公式如下：
函数原型：void asc_shiftleft(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, uint32_t distance, uint32_t count)
约束：distance不支持设置为负数。；distance取值不能超过src数据类型的位宽。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscShiftLeft](../reg/logic_compute/asc_shiftleft.md)（`same_topic`）：AscShiftLeft说明根据mask对输入数据src0按照src1对应元素进行左移操作，结果写入dst。
- [AscShiftLeftScalar](../reg/logic_compute/asc_shiftleft_scalar.md)（`same_topic`）：AscShiftLeftScalar 与《AscShiftleft》的衔接是：标量左移与张量左移、C Vector 标量版本以及右移对应接口共同界定移位量来源、方向和 Reg/Memory 执行契约。
- [ShiftLeft](../../basic_api/memory_vector_compute/logical_compute/shift_left.md)（`same_topic`）：ShiftLeft说明对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。
- [ShiftLeft](../../basic_api/memory_vector_compute/logical_compute/shift_left_shift_amount_tensor.md)（`same_topic`）：ShiftLeft 与《AscShiftleft》的实质衔接是：这些接口覆盖 tensor/标量移位量、Memory/Reg/C 路径及左右移方向，直接用于核对 ShiftLeft 的移位量来源与有符号/无符号语义。
<!-- cannbot:related:end -->
