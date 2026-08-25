---
type: API
title: __half2bfloat16_rz
description: 遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__half2bfloat16_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2bfloat16_rz

遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。
函数原型：bfloat16_t __half2bfloat16_rz(const half x)
返回值：输入遵循CAST_TRUNC模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__half2bfloat16_rna](_half2bfloat16_rna.md)（`related`）：《__half2bfloat16_rz》明确“遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。”；它与《__half2bfloat16_rna》的“遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
- [__half2bfloat16_rd](_half2bfloat16_rd.md)（`same_topic`）：《__half2bfloat16_rd》的任务是“遵循CAST_FLOOR模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rz》具体提供“遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，它直接用于half→bfloat16 的同源同目标舍入模式选择。
- [__half2bfloat16_rn](_half2bfloat16_rn.md)（`same_topic`）：两者都把 half 转 bfloat16，差异仅是 RZ 截断与 RN 最近舍入；需要按数值 oracle 选择舍入模式。
- [__half2bfloat16_ru](_half2bfloat16_ru.md)（`same_topic`）：《__half2bfloat16_ru》处理“遵循CAST_CEIL模式，将half类型数据转换为bfloat16类型，返回转换后的值。”。《__half2bfloat16_rz》明确提供“遵循CAST_TRUNC模式，将half类型数据转换为bfloat16类型，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 bfloat16 的同源同目标不同舍入模式。
<!-- cannbot:related:end -->
