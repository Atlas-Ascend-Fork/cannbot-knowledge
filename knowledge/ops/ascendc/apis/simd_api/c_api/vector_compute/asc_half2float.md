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

- [AscHalf2Float](../reg/data_type_convert/asc_half2float.md)（`related`）：两者都将 half 转 float；focal 在 Reg API 中按 VL 的奇偶半段布局展开，vector 版本直接处理内存矢量，适合按数据驻留位置选型。
- [__half2float](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2float.md)（`related`）：《__half2float》明确“将half类型数据转换为浮点数，返回转换后的值。”；它与《AscHalf2float》的“将half类型转化为float类型，无舍入模式。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
