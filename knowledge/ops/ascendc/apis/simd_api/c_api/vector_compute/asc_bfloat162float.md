---
type: API
title: AscBfloat162float
description: 将bfloat16_t类型数据转为float，无舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_bfloat162float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscBfloat162float

将bfloat16_t类型数据转为float，无舍入模式。
函数原型：void asc_bfloat162float(__ubuf__ float* dst, __ubuf__ bfloat16_t* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162float](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162float.md)（`related`）：Vector C API 提供 UB 批量 bfloat16→float，可与 SIMT 标量版本按访存布局和并行模型选择。
- [AscBfloat162Float](../reg/data_type_convert/asc_bfloat162float.md)（`same_topic`）：《AscBfloat162float》明确“将bfloat16_t类型数据转为float，无舍入模式。”；它与《AscBfloat162Float》的“将bfloat16_t类型转化为float类型，无舍入模式。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
