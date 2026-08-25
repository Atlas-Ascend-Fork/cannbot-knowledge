---
type: API
title: AscAddScalar
description: 执行矢量和标量的加法运算，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_add_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscAddScalar

执行矢量和标量的加法运算。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：mask未筛选的元素在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Adds（灵活标量位置）](../../../basic_api/memory_vector_compute/basic_arithmetic/adds_flexible_scalar.md)（`same_topic`）：Adds（灵活标量位置） 与《AscAddScalar》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
- [AscAdd](asc_add.md)（`same_topic`）：AscAdd 与《AscAddScalar》的实质衔接是：Reg、Vector 和 scalar 三种 AscAdd 入口实现相同加法，区别在操作数载体、mask 与结果位置。
- [AscAdd](../../vector_compute/asc_add.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddScalar》补充：执行矢量和标量的加法运算，将结果写入目的操作数dst。
- [AscAddScalar](../../vector_compute/asc_add_scalar.md)（`same_topic`）：Reg 与 Vector C API 都执行逐元素加标量，可据数据载体和 mask/repeat 模型迁移。
<!-- cannbot:related:end -->
