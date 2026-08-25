---
type: API
title: AscMinScalar
description: 源操作数矢量逐元素与标量相比，如果比标量值大，则取标量值，比标量值小，则取源操作数值。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_min_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscMinScalar

源操作数矢量逐元素与标量相比，如果比标量值大，则取标量值，比标量值小，则取源操作数值。计算公式如下：
函数原型：void asc_min_scalar(__ubuf__ half* dst, __ubuf__ half* src, half value, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscMaxScalar](asc_max_scalar.md)（`related`）：AscMaxScalar 是同一 Vector 标量比较模型的取大对偶，可据 clamp 上界或下界选择。
- [AscMin](asc_min.md)（`same_topic`）：AscMin 与《AscMinScalar》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [AscMinScalar](../reg/arithmetic_compute/asc_min_scalar.md)（`same_topic`）：AscMinScalar 与《AscMinScalar》的实质衔接是：AscMinScalar 在 Reg 上比较 vector 与 scalar；Vector 对应入口、tensor-tensor Min、MaxScalar 和灵活 Mins 分别界定执行层、操作数形态与相反边界。
- [Mins（灵活标量位置）](../../basic_api/memory_vector_compute/basic_arithmetic/mins_flexible_scalar.md)（`same_topic`）：MinsFlexibleScalar 提供 C++ Memory API 映射，并允许 scalar 来自 LocalTensor 单点或位于任一操作数位置。
<!-- cannbot:related:end -->
