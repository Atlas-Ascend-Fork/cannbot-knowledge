---
type: API
title: AscInt322int16
description: 将int32_t类型数据转换为int16_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int322int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt322int16

将int32_t类型数据转换为int16_t类型。
函数原型：void asc_int322int16(__ubuf__ int16_t* dst, __ubuf__ int32_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt322Int16](../reg/data_type_convert/asc_int322int16.md)（`same_topic`）：根据mask将src中的每个int32_t类型元素转化为int16_t类型，支持饱和/非饱和模式，结果写入dst；将int32_t类型数据转换为int16_t类型。两卡的核心转换都是 int32 到 int16；焦点补充 950 Reg mask、奇偶半 VL 与饱和模式，候选给出 A2/A3 UB 指针和 32B 对齐。
<!-- cannbot:related:end -->
