---
type: API
title: __hgt
description: 比较两个half类型数据，仅当第一个数大于第二个数时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hgt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgt

功能：比较两个half类型数据，仅当第一个数大于第二个数时，返回true。

函数原型：bool __hgt(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入的第一个数是否大于第二个数的结果。任一输入为nan时，返回false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hge](_hge.md)（`related`）：__hgt 与《__hge》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hgeu](_hgeu.md)（`related`）：__hgt 与《__hgeu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hgt](../../bfloat16_type/bfloat16_compare_functions/_hgt.md)（`related`）：__hgt 与《__hgt》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hgtu](_hgtu.md)（`related`）：__hgt 与《__hgtu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hle](_hle.md)（`related`）：__hgt 与《__hle》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hleu](_hleu.md)（`related`）：__hgt 与《__hleu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hlt](_hlt.md)（`related`）：__hgt 与《__hlt》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hltu](_hltu.md)（`related`）：__hgt 与《__hltu》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
<!-- cannbot:related:end -->
