---
type: API
title: __hneu
description: 比较两个half类型数据是否不相等，不相等时返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hneu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hneu

功能：比较两个half类型数据是否不相等，不相等时返回true。若任一输入为nan，返回true。

函数原型：bool __hneu(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据是否不相等的结果。任一输入为nan时返回true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hne](_hne.md)（`same_topic`）：《__hne》的任务是“比较两个half类型数据是否不相等，不相等时返回true。”。《__hneu》具体提供“比较两个half类型数据是否不相等，不相等时返回true。若任一输入为nan，返回true。”，它直接用于half 不等比较的有序/无序语义和 bfloat16 对应实现。
<!-- cannbot:related:end -->
