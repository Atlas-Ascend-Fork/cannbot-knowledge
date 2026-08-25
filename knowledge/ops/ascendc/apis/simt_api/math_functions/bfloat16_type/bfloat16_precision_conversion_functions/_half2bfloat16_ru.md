---
type: API
title: __half2bfloat16_ru
description: 遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__half2bfloat16_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2bfloat16_ru

遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。
函数原型：bfloat16_t __half2bfloat16_ru(const half x)
返回值：输入遵循CAST_CEIL模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Bfloat16](../../../../simd_api/c_api/reg/data_type_convert/asc_half2bfloat16.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《AscHalf2Bfloat16》明确提供“将half类型数据转为bfloat16类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
- [__half2bfloat16_rd](_half2bfloat16_rd.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rd》明确提供“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
- [__half2bfloat16_rn](_half2bfloat16_rn.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rn》明确提供“遵循CAST_RINT模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
- [__half2bfloat16_rna](_half2bfloat16_rna.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rna》明确提供“遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
- [__half2bfloat16_rz](_half2bfloat16_rz.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rz》明确提供“遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
<!-- cannbot:related:end -->
