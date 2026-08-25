---
type: API
title: AscLtScalar
description: 执行矢量中每个位置和标量比较，如果值小于标量值则为1，否则为0，结果为每个bit位按小端序排布。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_lt_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscLtScalar

执行矢量中每个位置和标量比较，如果值小于标量值则为1，否则为0，结果为每个bit位按小端序排布。
函数原型：void asc_lt_scalar(__ubuf__ uint8_t* dst, __ubuf__ half* src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscEqScalar](asc_eq_scalar.md)（`same_topic`）：AscEqScalar 与《AscLtScalar》的实质衔接是：AscEqScalar 与其他标量比较共享 scalar 广播和 mask 输出契约；vector-vector Eq、灵活标量 Compare/Select 说明比较源形态及结果消费方式。
- [AscLt](asc_lt.md)（`same_topic`）：AscLt 与《AscLtScalar》的实质衔接是：Reg 与 Vector AscLt 实现 vector-vector 小于比较，AscLtScalar 是标量右操作数的直接变体。
- [AscLtScalar](../reg/compare_and_select/asc_lt_scalar.md)（`same_topic`）：“AscLtScalar”定义：根据mask将源操作数src中元素逐个与标量value比较是否小于，比较结果写入dst对应比特位，成立为1，不成立为0。；“AscLtScalar”定义：执行矢量中每个位置和标量比较，如果值小于标量值则为1，否则为0，结果为每个bit位按小端序排布。。实质衔接：Vector 版保持 src 与 scalar 的 LT 语义但输出布局不同；Reg asc_lt 则把第二操作数改为寄存器，帮助选择正确重载。
<!-- cannbot:related:end -->
