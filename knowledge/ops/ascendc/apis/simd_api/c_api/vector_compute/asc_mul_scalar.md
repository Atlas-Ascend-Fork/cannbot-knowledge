---
type: API
title: AscMulScalar
description: 执行矢量与标量的乘法运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscMulScalar

执行矢量与标量的乘法运算。计算公式如下：
函数原型：void asc_mul_scalar(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, int16_t value, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscMul](../reg/arithmetic_compute/asc_mul.md)（`related`）：AscMulScalar 与《AscMul》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [AscMulScalar](../reg/arithmetic_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 与《AscMulScalar》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [AscMuls](../reg/arithmetic_compute/asc_muls_deprecated.md)（`related`）：AscMulScalar 与《AscMuls》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [Muls（灵活标量位置）](../../basic_api/memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`related`）：AscMulScalar 与《Muls（灵活标量位置）》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [AscMul](asc_mul.md)（`same_topic`）：AscMulScalar 与《AscMul》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
<!-- cannbot:related:end -->
