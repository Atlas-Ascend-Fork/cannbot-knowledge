---
type: API
title: __float2bfloat16_rna
description: 遵循CAST_ROUND模式，将浮点数转换为bfloat16精度，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2bfloat16_rna

遵循CAST_ROUND模式，将浮点数转换为bfloat16精度，返回转换后的值。
函数原型：bfloat16_t __float2bfloat16_rna(const float x)
返回值：输入遵循CAST_ROUND模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__float2bfloat16_rd](_float2bfloat16_rd.md)（`related`）：rna 使用 CAST_ROUND，与 rd 的向下取整在边界值上结果不同。
- [__float2bfloat16_rna_sat](_float2bfloat16_rna_sat.md)（`same_topic`）：《__float2bfloat16_rna_sat》明确“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_ROUND模式，返回转换后的值。”；它与《__float2bfloat16_rna》的“遵循CAST_ROUND模式，将浮点数转换为bfloat16精度，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
