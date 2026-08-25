---
type: API
title: AscMuls
description: 对源操作数src和标量value进行乘法运算再按ROUND舍入模式转成half类型，根据mask将结果写入目的操作数dst。已废弃。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_muls_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscMuls

对源操作数src和value进行乘法运算再按照数据类型转换的ROUND舍入模式转成half类型，根据mask将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMulScalar](../../vector_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 与《AscMuls》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [Muls](../../../basic_api/memory_vector_compute/basic_arithmetic/muls.md)（`related`）：Memory Muls 在 LocalTensor 上执行矢量标量乘法，可在不显式管理寄存器时替代废弃 C Reg 形态。
- [Muls](../../../basic_api/reg_vector_compute/basic_arithmetic/muls.md)（`related`）：废弃 C AscMuls 的目标能力由 Reg C++ Muls 表达：按 mask 将 RegTensor 与标量相乘，避免继续依赖废弃接口。
- [Muls（灵活标量位置）](../../../basic_api/memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`related`）：Muls（灵活标量位置） 与《AscMuls》的实质衔接是：灵活标量 Muls 的 scalarTensorIndex、LocalTensor 单点标量和 cyclic-repeat 语义会直接影响广播乘法、量化 scale 与标量位置。
- [AscMulScalar](asc_mul_scalar.md)（`same_topic`）：AscMulScalar 与《AscMuls》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
<!-- cannbot:related:end -->
