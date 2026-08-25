---
type: API
title: AscNeScalar
description: 将源操作数src中每个元素逐个与标量value比较是否不相等，若不相等则dst对应比特位为1，否则为0。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_ne_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscNeScalar

src 中的每个元素逐个与标量 value 比较是否不相等，如果 src_i != value，则输出结果 dst 对应比特位为1，否则为0，每个元素的比较结果占一个bit。dst 为掩码寄存器，按掩码 mask 指示参与计算的元素。

参数：dst(输出): 目的操作数（掩码寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

约束：- mask未筛选的元素在输出中置零。
- 浮点数据类型比较，涉及nan时比较结果为1。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscNeScalar](../../vector_compute/asc_ne_scalar.md)（`related`）：Reg 版本执行相同 vector-scalar 不等比较，但输入输出驻留寄存器；Memory 版本操作 UB 指针。
- [Compare](../../../basic_api/memory_vector_compute/compare_and_select/compare.md)（`related`）：Compare说明逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
- [AscEqScalar](../../vector_compute/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscNeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscNe](asc_ne.md)（`same_topic`）：AscNe说明逐元素比较两个源操作数是否不相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。
- [ComparesFlexibleScalar](../../../basic_api/memory_vector_compute/compare_and_select/compares_flexible_scalar.md)（`same_topic`）：ComparesFlexibleScalar说明提供灵活标量位置的Compares接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
<!-- cannbot:related:end -->
