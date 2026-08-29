---
type: API
title: AscNeScalar
description: src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_ne_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscNeScalar

src中的每个元素逐个与标量value比较大小，如果某个位置上的元素不等于value，则输出结果dst对应比特位为1，否则为0。
函数原型：void asc_ne_scalar(__ubuf__ uint8_t *dst, __ubuf__ half *src, half value, uint8_t repeat, uint16_t dst_block_stride, uint16_t src_block_stride, uint16_t dst_repeat_stride, uint16_t src_repeat_stride)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。；dst按照小端顺序排序成二进制结果，对应src中相应位置的数据比较结果。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
