---
type: API
title: AscAddScalar
description: 执行矢量与标量的加法运算，支持连续数据计算、高维切分计算和同步计算模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_add_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAddScalar

执行矢量加法运算。计算公式如下：
函数原型：void asc_add_scalar(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, int16_t value, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Adds（灵活标量位置）](../../basic_api/memory_vector_compute/basic_arithmetic/adds_flexible_scalar.md)（`same_topic`）：Adds（灵活标量位置） 与《AscAddScalar》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
- [AscAdd](../reg/arithmetic_compute/asc_add.md)（`same_topic`）：AscAdd说明根据mask对源操作数src0、src1按元素求和，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscAdd](asc_add.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddScalar》补充：执行矢量与标量的加法运算，支持连续数据计算、高维切分计算和同步计算模式。
- [AscAddScalar](../reg/arithmetic_compute/asc_add_scalar.md)（`same_topic`）：Reg 与 Vector C API 都执行逐元素加标量，可据数据载体和 mask/repeat 模型迁移。
<!-- cannbot:related:end -->
