---
type: API
title: AscFloat2int32
description: 将float类型转化为int32_t类型，并支持多种舍入模式： * RINT舍入模式：四舍六入五成双舍入 * ROUND舍入模式：四舍五入舍入
  * FLOOR舍入模式：向负无穷舍入 * CEIL舍入模式：向正无穷舍入 * TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFloat2int32

将float类型转化为int32_t类型，并支持多种舍入模式： RINT舍入模式：四舍六入五成双舍入 ROUND舍入模式：四舍五入舍入
函数原型：void asc_float2int32_rn(__ubuf__ int32_t* dst, __ubuf__ float* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](../reg/data_type_convert/asc_float2int32.md)（`same_topic`）：将float类型转化为int32_t类型，并支持多种舍入模式： RINT舍入模式：四舍六入五成双舍入 ROUND舍入模式：四舍五入舍入；将float类型数据转化为int32_t类型，并支持多种舍入模式，饱和/非饱和模式。。两卡围绕同一 float 到 int32 转换及舍入契约，Reg 版本进一步明确饱和模式。
<!-- cannbot:related:end -->
