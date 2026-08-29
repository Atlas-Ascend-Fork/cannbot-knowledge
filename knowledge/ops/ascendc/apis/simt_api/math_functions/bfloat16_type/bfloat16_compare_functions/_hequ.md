---
type: API
title: __hequ
description: 比较两个bfloat16类型数据是否相等，相等时返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hequ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequ

比较两个bfloat16类型数据是否相等，相等时返回true。若任一输入为nan，返回true。
函数原型：bool __hequ(bfloat16_t x, bfloat16_t y)
返回值：比较输入数据是否相等的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__heq](_heq.md)（`same_topic`）：比较两个bfloat16类型数据是否相等，相等时返回true。；比较两个bfloat16类型数据是否相等，相等时返回true。若任一输入为nan，返回true。。两者都是 bfloat16 标量相等比较，差别在有序版本遇 NaN 为 false、无序版本遇 NaN 为 true，是同一决策点的语义变体。
<!-- cannbot:related:end -->
