---
type: API
title: AscMul
description: asc_mul（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscMul

执行矢量乘法运算。计算公式如下
函数原型：void asc_mul(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：AscMul 与《MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [AscMulScalar](../reg/arithmetic_compute/asc_mul_scalar.md)（`related`）：AscMulScalar 与《AscMul》的实质衔接是：Reg AscMulScalar 与 Vector/Reg tensor-tensor/Muls 入口共享逐 lane 乘法；cyclic-repeat scale 故障直接约束标量分组广播的计算范围。
- [AscMul](../reg/arithmetic_compute/asc_mul.md)（`same_topic`）：AscMul 与《AscMul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [AscMulCastHalf2int8](asc_mul_cast_half2int8.md)（`same_topic`）：AscMulCastHalf2int8 与《AscMul》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [AscMulScalar](asc_mul_scalar.md)（`same_topic`）：AscMulScalar 与《AscMul》的实质衔接是：Vector AscMulScalar 与 Reg scalar、tensor-tensor、废弃 Muls 和灵活标量 Muls 共享矢量乘标量任务；scale 错配卡验证重复广播边界。
- [Mul](../../basic_api/memory_vector_compute/basic_arithmetic/mul.md)（`same_topic`）：AscMul 与《Mul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [Mul](../../basic_api/reg_vector_compute/basic_arithmetic/mul.md)（`same_topic`）：AscMul 与《Mul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
<!-- cannbot:related:end -->
