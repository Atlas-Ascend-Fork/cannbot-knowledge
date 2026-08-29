---
type: API
title: __half2bfloat16_rna
description: 遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__half2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2bfloat16_rna

遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。
函数原型：bfloat16_t __half2bfloat16_rna(const half x)
返回值：输入遵循CAST_ROUND模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__half2bfloat16_rn](_half2bfloat16_rn.md)（`same_topic`）：遵循CAST_RINT模式，将half类型数据转换为bfloat16类型，返回转换后的值。；遵循CAST_ROUND模式，将half类型数据转换为bfloat16类型，返回转换后的值。。两端具有相同 half 到 bfloat16 转换合同，只在 CAST_RINT 与 CAST_ROUND 舍入规则上分流，互读可按数值舍入要求选择入口。
<!-- cannbot:related:end -->
