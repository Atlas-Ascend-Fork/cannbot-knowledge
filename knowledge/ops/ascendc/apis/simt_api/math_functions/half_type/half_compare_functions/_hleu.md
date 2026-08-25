---
type: API
title: __hleu
description: 比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hleu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hleu

功能：比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。

函数原型：bool __hleu(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入的第一个数是否小于或等于第二个数的结果。任一输入为nan时返回true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__heq](_heq.md)（`related`）：《__heq》明确“比较两个half类型数据是否相等，相等时返回true。”；它与《__hleu》的“比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hge](_hge.md)（`related`）：《__hge》明确“比较两个half类型数据，仅当第一个数大于或等于第二个数时，返回true。”；它与《__hleu》的“比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hgt](_hgt.md)（`related`）：__hgt 与《__hleu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hequ](_hequ.md)（`same_topic`）：《__hequ》明确“比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。”；它与《__hleu》的“比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hle](_hle.md)（`same_topic`）：__hle 与 __hleu 的有限值比较相同，关键差异是任一 NaN 时前者 false、后者 true，直接决定 ordered/unordered 比较选择。
<!-- cannbot:related:end -->
