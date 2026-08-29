---
type: API
title: AscOr
description: 每对元素按位或运算，
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_or.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscOr

每对元素按位或运算，计算公式如下：
函数原型：void asc_or(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscOr](../reg/logic_compute/asc_or.md)（`same_topic`）：每对元素按位或运算，计算公式如下：；根据mask对源操作数src0、src1执行按位或（｜）操作，将结果写入目的操作数dst。。两张 C API 卡的核心运算都是逐元素按位或，Reg 版本进一步显式给出 mask、源寄存器和目的寄存器契约。
<!-- cannbot:related:end -->
