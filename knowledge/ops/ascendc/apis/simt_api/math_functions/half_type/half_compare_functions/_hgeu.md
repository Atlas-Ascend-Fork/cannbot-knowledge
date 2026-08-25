---
type: API
title: __hgeu
description: 比较两个half类型数据，当第一个数大于或等于第二个数时，返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hgeu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgeu

功能：比较两个half类型数据，当第一个数大于或等于第二个数时，返回true。若任一输入为nan，返回true。

函数原型：bool __hgeu(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入的第一个数是否大于或等于第二个数的结果。特殊值：x<y→false；x>y→true；x=y→true；任一值为nan→true；±0→true；inf→true；-inf→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgt](_hgt.md)（`related`）：__hgt 与《__hgeu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hge](_hge.md)（`same_topic`）：__hgeu 的核心契约是“比较两个half类型数据，当第一个数大于或等于第二个数时，返回true。若任一输入为nan，返回true”；__hge 补充“比较两个half类型数据，仅当第一个数大于或等于第二个数时，返回true”。
- [__hgeu](../../bfloat16_type/bfloat16_compare_functions/_hgeu.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hgeu》提供“比较两个half类型数据，当第一个数大于或等于第二个数时，返回true。若任一输入为nan，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
<!-- cannbot:related:end -->
