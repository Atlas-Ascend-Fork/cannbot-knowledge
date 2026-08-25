---
type: API
title: AscLeScalar
description: 按元素判断src <= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_le_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscLeScalar

按元素判断src <= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。
函数原型：void asc_le_scalar(__ubuf__ uint8_t* dst, __ubuf__ half* src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；value（输入）：源操作数（标量）。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscLe](asc_le.md)（`related`）：AscLeScalar 把第二个 Tensor 换为标量 value；阈值比较无需广播 Tensor 时可直接使用。
- [AscLeScalar](../reg/compare_and_select/asc_le_scalar.md)（`related`）：AscLeScalar 与《AscLeScalar》的实质衔接是：Reg 与 Vector C API 及 ComparesFlexibleScalar 都实现 vector≤scalar，区别在结果载体与编程层级。
- [ComparesFlexibleScalar](../../basic_api/memory_vector_compute/compare_and_select/compares_flexible_scalar.md)（`related`）：AscLeScalar 与《ComparesFlexibleScalar》的实质衔接是：Reg 与 Vector C API 及 ComparesFlexibleScalar 都实现 vector≤scalar，区别在结果载体与编程层级。
- [AscEqScalar](asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscLeScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLe](../reg/compare_and_select/asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscLeScalar正文说明“按元素判断src <= value是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
<!-- cannbot:related:end -->
