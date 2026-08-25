---
type: API
title: AscMul
description: 根据mask对源操作数src0、src1按元素进行乘法运算，将结果写入目的操作数dst。仅在AIV上生效。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscMul

该接口根据mask，对源操作数src0、src1按元素进行乘法运算，将结果写入目的操作数dst。

本接口仅在AIV上生效。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half。

约束：- 本接口在非AIV上调用直接返回。
- mask需通过掩码设置接口预先赋值后再传入，未赋值的掩码寄存器内容不确定，会导致有效元素位置错误。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMulCastHalf2uint8](../../vector_compute/asc_mul_cast_half2uint8.md)（`related`）：MulCast 在乘法后直接压缩到 uint8，而 Reg AscMul 仅保留乘积；需要融合量化输出时应选前者。
- [AscMulScalar](../../vector_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 与《AscMul》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [AscMul](../../vector_compute/asc_mul.md)（`same_topic`）：AscMul 与《AscMul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [AscMulScalar](asc_mul_scalar.md)（`same_topic`）：AscMulScalar 与《AscMul》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [Mul](../../../basic_api/reg_vector_compute/basic_arithmetic/mul.md)（`same_topic`）：Mul 与《AscMul》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
<!-- cannbot:related:end -->
