---
type: API
title: __habs
description: 获取输入数据的绝对值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_arithmetic_functions/__habs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __habs

获取输入数据的绝对值。
函数原型：bfloat16_t __habs(bfloat16_t x)
返回值：输入数据的绝对值。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__habsx2](../bfloat16x2_arithmetic_functions/_habsx2.md)（`related`）：标量 bfloat16 版本只处理一个分量，可按是否需要成对并行选择。
- [__habs](../../half_type/half_arithmetic_functions/_habs.md)（`same_topic`）：half 与 bfloat16 标量 Abs 完成相同绝对值运算，源精度不同。
<!-- cannbot:related:end -->
