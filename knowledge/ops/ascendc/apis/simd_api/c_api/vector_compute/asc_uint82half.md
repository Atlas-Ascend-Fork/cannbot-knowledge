---
type: API
title: AscUint82half
description: 将uint8_t类型数据转换为half类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_uint82half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscUint82half

将uint8_t类型数据转换为half类型。
函数原型：void asc_uint82half(__ubuf__ half* dst, __ubuf__ uint8_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Uint8](../reg/data_type_convert/asc_half2uint8.md)（`related`）：half→uint8 是反向量化/转换路径，舍入和饱和语义需与 uint8→half 往返需求配套验证。
- [AscInt82half](asc_int82half.md)（`related`）：int8→half 与 uint8→half 的目标类型相同，但源有符号性影响数值解释，迁移时需明确 dtype。
- [AscUint82half](../reg/data_type_convert/asc_uint82half.md)（`related`）：Vector C API 提供同一 uint8→half 转换，但数据载体与分片方式不同，可对照 Reg 版本的 1:2 位宽处理。
<!-- cannbot:related:end -->
