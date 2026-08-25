---
type: API
title: __hle
description: 比较两个half类型数据，仅当第一个数小于或等于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hle

功能：比较两个half类型数据，仅当第一个数小于或等于第二个数时，返回true。

函数原型：bool __hle(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入的第一个数是否小于或等于第二个数的结果。任一输入为nan时返回false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgt](_hgt.md)（`related`）：__hgt 与《__hle》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hle](../../bfloat16_type/bfloat16_compare_functions/_hle.md)（`related`）：half __hle 与 BF16 __hle 具有相同 ordered <= 和 NaN=false 契约，可在低精度 dtype 切换时保持比较语义。
- [__hleu](_hleu.md)（`same_topic`）：__hle 与 __hleu 的有限值比较相同，关键差异是任一 NaN 时前者 false、后者 true，直接决定 ordered/unordered 比较选择。
<!-- cannbot:related:end -->
