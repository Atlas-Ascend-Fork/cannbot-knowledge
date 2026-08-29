---
type: API
title: AscDeqInt322half
description: 对输入的int32_t类型的数据按元素做量化并转换为half类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_deq_int322half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscDeqInt322half

对输入的int32_t类型的数据按元素做量化并转换为half类型。计算公式如下： 其中的scale可通过asc_set_deq_scale设置。
函数原型：void asc_deq_int322half(__ubuf__ half* dst, __ubuf__ int32_t* src, uint32_t count)
约束：需配合asc_set_deq_scale接口的非向量模式使用，该接口用于设置量化参数。；dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
