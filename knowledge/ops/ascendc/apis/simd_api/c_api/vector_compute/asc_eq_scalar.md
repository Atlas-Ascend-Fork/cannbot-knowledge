---
type: API
title: AscEqScalar
description: 按元素判断src = value是否成立，若成立则输出结果的对应比特位为1，否则为0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_eq_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscEqScalar

按元素判断src = value是否成立，若成立则输出结果的对应比特位为1，否则为0。
函数原型：void asc_eq_scalar(__ubuf__ uint8_t* dst, __ubuf__ half* src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscNeScalar](asc_ne_scalar.md)（`related`）：EqScalar 与 NeScalar 共享标量比较和 bit 结果布局，提供互补的相等/不等分支。
- [AscEq](../reg/compare_and_select/asc_eq.md)（`same_topic`）：AscEqScalar 与《AscEq》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscEq](asc_eq.md)（`same_topic`）：AscEqScalar 与《AscEq》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscEqScalar](../reg/compare_and_select/asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscEqScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGeScalar](../reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：AscEqScalar 与《AscGeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGeScalar](asc_ge_scalar.md)（`same_topic`）：AscEqScalar 与《AscGeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGtScalar](../reg/compare_and_select/asc_gt_scalar.md)（`same_topic`）：AscEqScalar 与《AscGtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscGtScalar](asc_gt_scalar.md)（`same_topic`）：AscEqScalar 与《AscGtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLeScalar](../reg/compare_and_select/asc_le_scalar.md)（`same_topic`）：AscEqScalar 与《AscLeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLeScalar](asc_le_scalar.md)（`same_topic`）：AscEqScalar 与《AscLeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLtScalar](../reg/compare_and_select/asc_lt_scalar.md)（`same_topic`）：AscEqScalar 与《AscLtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLtScalar](asc_lt_scalar.md)（`same_topic`）：AscEqScalar 与《AscLtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscNeScalar](../reg/compare_and_select/asc_ne_scalar.md)（`same_topic`）：AscEqScalar 与《AscNeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [ComparesFlexibleScalar](../../basic_api/memory_vector_compute/compare_and_select/compares_flexible_scalar.md)（`same_topic`）：AscEqScalar 与《ComparesFlexibleScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [SelectFlexibleScalar](../../basic_api/memory_vector_compute/compare_and_select/select_flexible_scalar.md)（`same_topic`）：AscEqScalar 与《SelectFlexibleScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
<!-- cannbot:related:end -->
