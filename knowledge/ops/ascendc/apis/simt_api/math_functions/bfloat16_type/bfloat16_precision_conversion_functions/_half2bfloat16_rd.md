---
type: API
title: __half2bfloat16_rd
description: 遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__half2bfloat16_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2bfloat16_rd

遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。
函数原型：bfloat16_t __half2bfloat16_rd(const half x)
返回值：输入遵循CAST_FLOOR模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Bfloat16](../../../../simd_api/c_api/reg/data_type_convert/asc_half2bfloat16.md)（`related`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《AscHalf2Bfloat16》具体提供“将half类型数据转为bfloat16类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
- [__bfloat162bfloat16_rd](_bfloat162bfloat16_rd.md)（`related`）：__half2bfloat16_rd 把 half 按 CAST_FLOOR 转入 bfloat16，可与 focal 的 bfloat16 域取整组成混合低精度路径。
- [__half2bfloat16_rn](_half2bfloat16_rn.md)（`same_topic`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rn》具体提供“遵循CAST_RINT模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
- [__half2bfloat16_rna](_half2bfloat16_rna.md)（`same_topic`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rna》具体提供“遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
- [__half2bfloat16_ru](_half2bfloat16_ru.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rd》明确提供“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
- [__half2bfloat16_rz](_half2bfloat16_rz.md)（`same_topic`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rz》具体提供“遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
<!-- cannbot:related:end -->
