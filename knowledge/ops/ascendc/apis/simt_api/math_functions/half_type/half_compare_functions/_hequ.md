---
type: API
title: __hequ
description: 比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hequ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequ

功能：比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。

函数原型：bool __hequ(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据是否相等的结果。特殊值：±0→true；inf→true；-inf→true；inf→false；-inf→false；ASCRT_MAX_NORMAL_FP16→true；ASCRT_MAX_NORMAL_FP16→false；(1,ASCRT_MAX_NORMAL_FP16)→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__heq](_heq.md)（`same_topic`）：__hequ 与 __heq 均判断 half 相等，唯一关键差异是 NaN 时 unordered 版本为真、ordered 版本为假。
- [__hleu](_hleu.md)（`same_topic`）：《__hequ》明确“比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。”；它与《__hleu》的“比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
