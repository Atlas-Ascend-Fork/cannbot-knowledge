---
type: API
title: AscSubScalar
description: 执行矢量和标量的减法运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_sub_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSubScalar

执行矢量和标量的减法运算。
函数原型：void asc_sub_scalar(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, int16_t value, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSub](../reg/arithmetic_compute/asc_sub.md)（`same_topic`）：AscSub说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscSub](asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSubScalar》补充：执行矢量和标量的减法运算。
- [Subs（灵活标量位置）](../../basic_api/memory_vector_compute/basic_arithmetic/subs_flexible_scalar.md)（`same_topic`）：Subs（灵活标量位置）说明矢量元素与标量做减法，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
<!-- cannbot:related:end -->
