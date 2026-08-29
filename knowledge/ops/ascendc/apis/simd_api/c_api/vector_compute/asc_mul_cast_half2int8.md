---
type: API
title: AscMulCastHalf2int8
description: 按元素求积，并将结果转换为int8_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul_cast_half2int8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscMulCastHalf2int8

按元素求积，并将结果转换为int8_t类型。计算公式如下： 精度转换规则：将源操作数的乘积按照RINT舍入模式（四舍六入五成双舍入），溢出做饱和处理。
函数原型：void asc_mul_cast_half2int8(__ubuf__ int8_t* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
