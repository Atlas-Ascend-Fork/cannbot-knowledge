---
type: API
title: AscHalf2float
description: 将half类型转化为float类型，无舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscHalf2float

将half类型转化为float类型，无舍入模式。
函数原型：void asc_half2float(__ubuf__ float* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Float](../reg/data_type_convert/asc_half2float.md)（`same_topic`）：将half类型转化为float类型，无舍入模式。；将half类型数据转换为float类型，无舍入模式。。两卡核心转换均为 half 到 float 且无舍入模式，分别覆盖 A2/A3 的 UB 向量接口与 950 的寄存器接口。
<!-- cannbot:related:end -->
