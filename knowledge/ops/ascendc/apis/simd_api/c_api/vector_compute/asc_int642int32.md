---
type: API
title: AscInt642int32
description: 将int64_t类型数据转换为int32_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int642int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt642int32

将int64_t类型数据转换为int32_t类型。
函数原型：void asc_int642int32(__ubuf__ int32_t* dst, __ubuf__ int64_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt642int32](../reg/data_type_convert/asc_int642int32.md)（`same_topic`）：将int64_t类型的源操作数转换成int32_t类型，并支持不同的饱和模式；将int64_t类型数据转换为int32_t类型。两端定义相同的 int64_t 到 int32_t 转换，分别给出 register 与 vector C API 形态。
<!-- cannbot:related:end -->
