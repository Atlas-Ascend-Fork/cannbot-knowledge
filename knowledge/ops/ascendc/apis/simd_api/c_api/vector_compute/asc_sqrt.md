---
type: API
title: AscSqrt
description: asc_sqrt（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_sqrt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscSqrt

按元素做开方，计算公式如下：
函数原型：void asc_sqrt(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：src只支持设置为正数。；操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSqrt](../reg/arithmetic_compute/asc_sqrt.md)（`same_topic`）：按元素做开方，计算公式如下：；该接口根据mask，对源操作数src进行按元素求开方操作，将结果写入目的操作数dst。两卡实现相同逐元素平方根；候选给出 950 Reg+mask 与负数/负零行为，焦点给出 A2/A3 UB 地址+count 与对齐约束。
<!-- cannbot:related:end -->
