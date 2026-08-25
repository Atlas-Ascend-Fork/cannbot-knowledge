---
type: API
title: AscLt
description: 按元素判断src0 < src1是否成立，若成立则输出结果dst上的对应比特位为1，否则为0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_lt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscLt

按元素判断src0 < src1是否成立，若成立则输出结果dst上的对应比特位为1，否则为0。
函数原型：void asc_lt(__ubuf__ half* src0, __ubuf__ half* src1, uint8_t repeat, uint8_t dst_block_stride, uint8_t src0_block_stride, uint8_t src1_block_stride, uint8_t dst_repeat_stride, uint8_t src0_repeat_stride, uint8_t src1_repeat_stride)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscLt](../reg/compare_and_select/asc_lt.md)（`related`）：AscLt 与《AscLt》的实质衔接是：Reg 与 Vector AscLt 实现 vector-vector 小于比较，AscLtScalar 是标量右操作数的直接变体。
- [AscLtScalar](asc_lt_scalar.md)（`same_topic`）：AscLt 与《AscLtScalar》的实质衔接是：Reg 与 Vector AscLt 实现 vector-vector 小于比较，AscLtScalar 是标量右操作数的直接变体。
<!-- cannbot:related:end -->
