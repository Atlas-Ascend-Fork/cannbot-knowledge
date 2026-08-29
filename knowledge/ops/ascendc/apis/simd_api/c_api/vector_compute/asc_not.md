---
type: API
title: AscNot
description: asc_not（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_not.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscNot

按元素做按位取反，计算公式如下。
函数原型：void asc_not(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscNot](../reg/logic_compute/asc_not.md)（`same_topic`）：按元素做按位取反；该接口用于对源操作数src执行按位取反操作，将结果写入目的操作数dst。。两者执行相同按位取反，前者使用 UB 地址与 count，后者使用 RegTensor 与 mask，可按 A2/A3 Vector 和 950 Reg 路线选择。
<!-- cannbot:related:end -->
