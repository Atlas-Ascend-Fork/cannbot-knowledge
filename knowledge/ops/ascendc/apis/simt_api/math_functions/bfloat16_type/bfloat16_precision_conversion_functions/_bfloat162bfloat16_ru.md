---
type: API
title: __bfloat162bfloat16_ru
description: 将bfloat16_t数据遵循CAST_CEIL模式取整。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162bfloat16_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162bfloat16_ru

将bfloat16_t数据遵循CAST_CEIL模式取整。
函数原型：bfloat16_t __bfloat162bfloat16_ru(const bfloat16_t x)
返回值：输入遵循CAST_CEIL模式取整后的bfloat16_t类型数据。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__bfloat162bfloat16_rd](_bfloat162bfloat16_rd.md)（`same_topic`）：__bfloat162bfloat16_rd说明将bfloat16_t数据遵循CAST_FLOOR模式取整；对__bfloat162bfloat16_ru而言，四个同源同目的转换只改变 floor、nearest、nearest-away 与 trunc 舍入决策，需并列选择而不能默认等价。
- [__bfloat162bfloat16_rn](_bfloat162bfloat16_rn.md)（`same_topic`）：__bfloat162bfloat16_rn说明将bfloat16_t数据遵循CAST_RINT模式取整；对__bfloat162bfloat16_ru而言，四个同源同目的转换只改变 floor、nearest、nearest-away 与 trunc 舍入决策，需并列选择而不能默认等价。
- [__bfloat162bfloat16_rna](_bfloat162bfloat16_rna.md)（`same_topic`）：__bfloat162bfloat16_rna说明将bfloat16_t数据遵循CAST_ROUND模式取整；对__bfloat162bfloat16_ru而言，四个同源同目的转换只改变 floor、nearest、nearest-away 与 trunc 舍入决策，需并列选择而不能默认等价。
- [__bfloat162bfloat16_rz](_bfloat162bfloat16_rz.md)（`same_topic`）：__bfloat162bfloat16_rz说明将bfloat16_t数据遵循CAST_TRUNC模式取整；对__bfloat162bfloat16_ru而言，四个同源同目的转换只改变 floor、nearest、nearest-away 与 trunc 舍入决策，需并列选择而不能默认等价。
<!-- cannbot:related:end -->
