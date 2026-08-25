---
type: API
title: AscMulScalar
description: 对源操作数src与标量value按元素做乘法运算，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_mul_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMulScalar

对源操作数src、value进行按元素做乘操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：mask对应位置为0的元素不参与计算，且在输出中置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMul](../../vector_compute/asc_mul.md)（`related`）：AscMulScalar 与《AscMul》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [AscMulScalar](../../vector_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 与《AscMulScalar》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [Muls](../../../basic_api/reg_vector_compute/basic_arithmetic/muls.md)（`related`）：AscMulScalar 是 C Reg API 的对应标量乘接口，可用于从 C++ Reg::Muls 迁移。
- [AscMul](asc_mul.md)（`same_topic`）：AscMulScalar 与《AscMul》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [AscMuls](asc_muls_deprecated.md)（`same_topic`）：AscMulScalar 与《AscMuls》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
<!-- cannbot:related:end -->
