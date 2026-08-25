---
type: API
title: __heq
description: 比较两个half类型数据是否相等，相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__heq.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heq

功能：比较两个half类型数据是否相等，相等时返回true。

函数原型：bool __heq(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据是否相等的结果，饱和与非饱和模式行为一致。特殊值：x=y，均为非nan的有限值→true；x≠y，均为非nan的有限值→false；±0→true；inf→true；-inf→true；inf→false；任一操作数为nan→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__heq](../../bfloat16_type/bfloat16_compare_functions/_heq.md)（`related`）：《__heq》处理“比较两个bfloat16类型数据是否相等，相等时返回true。”。《__heq》明确提供“比较两个half类型数据是否相等，相等时返回true。”，其参数、调用或验证步骤直接接入bfloat16x2 相等比较的有序/无序语义、互补关系和 half2 对应实现。
- [__hge](_hge.md)（`related`）：>= 包含大小关系而非只判相等。
- [__hisnan](_hisnan.md)（`related`）：IsNaN 可显式验证 Eq/Equ 的 NaN 分支。
- [__hleu](_hleu.md)（`related`）：《__heq》明确“比较两个half类型数据是否相等，相等时返回true。”；它与《__hleu》的“比较两个half类型数据，当第一个数小于或等于第二个数时，返回true。若任一输入为nan，返回true。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hne](_hne.md)（`related`）：《__hne》的任务是“比较两个half类型数据是否不相等，不相等时返回true。”。《__heq》具体提供“比较两个half类型数据是否相等，相等时返回true。”，它直接用于half 不等比较的有序/无序语义和 bfloat16 对应实现。
- [__hequ](_hequ.md)（`same_topic`）：__hequ 与 __heq 均判断 half 相等，唯一关键差异是 NaN 时 unordered 版本为真、ordered 版本为假。
<!-- cannbot:related:end -->
