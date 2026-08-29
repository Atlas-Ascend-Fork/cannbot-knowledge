---
type: API
title: __hne
description: 比较两个bfloat16类型数据是否不相等，不相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hne.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hne

比较两个bfloat16类型数据是否不相等，不相等时返回true。
函数原型：bool __hne(bfloat16_t x, bfloat16_t y)
返回值：输入数据是否不相等的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hneu](_hneu.md)（`same_topic`）：比较两个bfloat16类型数据是否不相等，不相等时返回true。 比较两个bfloat16类型数据是否不相等，不相等时返回true。若任一输入为nan，返回true。 共同的 BF16 不等运算把选型差异限定到 __hneu 的 unordered NaN 为 true，特殊值测试可据此设计。
<!-- cannbot:related:end -->
