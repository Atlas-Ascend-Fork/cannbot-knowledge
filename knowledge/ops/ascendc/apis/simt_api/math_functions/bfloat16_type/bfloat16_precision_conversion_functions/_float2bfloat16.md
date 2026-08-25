---
type: API
title: __float2bfloat16
description: 遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2bfloat16

遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值。
函数原型：bfloat16_t __float2bfloat16(const float x)
返回值：输入遵循CAST_RINT模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float2bfloat162_rn](_float2bfloat162_rn.md)（`related`）：__float2bfloat162_rn 与《__float2bfloat16》的实质衔接是：单个 float 填充 bf16x2 的 RNE 转换与双 float、双标量打包、标量转换和反向解包共享分量顺序与舍入契约。
- [AscFloat2Bfloat16](../../../../simd_api/c_api/reg/data_type_convert/asc_float2bfloat16.md)（`same_topic`）：AscFloat2Bfloat16 与 __float2bfloat16 都执行 float→bfloat16 转换；前者是带 mask 和可选舍入/饱和的 Reg 向量入口，后者是固定 CAST_RINT 的 SIMT 标量入口。
- [AscFloat2bfloat16](../../../../simd_api/c_api/vector_compute/asc_float2bfloat16.md)（`same_topic`）：__float2bfloat16 的核心契约是“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值”；AscFloat2bfloat16 补充“将float类型数据转换为bfloat16_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。
- [__float2bfloat16_rd](_float2bfloat16_rd.md)（`same_topic`）：__float2bfloat16 的核心契约是“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值”；__float2bfloat16_rd 补充“遵循CAST_FLOOR模式，将浮点数转换为bfloat16精度，返回转换后的值”。
- [__float2bfloat16_rn](_float2bfloat16_rn.md)（`same_topic`）：__float2bfloat16 的核心契约是“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值”；__float2bfloat16_rn 补充“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值”。
<!-- cannbot:related:end -->
