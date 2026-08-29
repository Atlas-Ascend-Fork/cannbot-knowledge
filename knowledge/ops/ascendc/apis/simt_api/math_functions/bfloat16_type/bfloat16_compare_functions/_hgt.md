---
type: API
title: __hgt
description: 比较两个bfloat16类型数据，仅当第一个数据大于第二个数据时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hgt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgt

比较两个bfloat16类型数据，仅当第一个数据大于第二个数据时，返回true。
函数原型：bool __hgt(bfloat16_t x, bfloat16_t y)
返回值：比较输入的第一个数是否大于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hgtu](_hgtu.md)（`related`）：比较两个bfloat16类型数据，当第一个数据大于第二个数据时，返回true。若任一输入为nan，返回true。；比较两个bfloat16类型数据，仅当第一个数据大于第二个数据时，返回true。两页是同一 bfloat16 大于比较的 unordered 与 ordered 选择，NaN 返回差异是实现正确性所需的关键决策。
<!-- cannbot:related:end -->
