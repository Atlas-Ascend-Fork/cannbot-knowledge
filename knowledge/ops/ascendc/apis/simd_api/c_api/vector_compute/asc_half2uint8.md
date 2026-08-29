---
type: API
title: AscHalf2uint8
description: 将 half 转换为 uint8_t，并支持 NONE、RINT、ROUND、FLOOR、CEIL 和 TRUNC 舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_half2uint8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscHalf2uint8

将half类型数据转换为uint8_t类型，支持多种舍入模式：
函数原型：void asc_half2uint8(__ubuf__ uint8_t* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Uint8](../reg/data_type_convert/asc_half2uint8.md)（`same_topic`）：将half类型数据转换为uint8类型，支持多种舍入模式，饱和/非饱和模式。；将half类型数据转换为uint8_t类型，支持多种舍入模式：。两卡处理同一 half→uint8 转换主题，但分别面向 950 寄存器操作数与 A2/A3 UB 向量地址，便于按平台和执行表面选用。
<!-- cannbot:related:end -->
