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

- [__hge](_hge.md)（`related`）：__hge 将严格大于扩展为大于等于，帮助根据边界相等时的预期选择比较谓词。
- [__hgt](../../half_type/half_compare_functions/_hgt.md)（`related`）：__hgt 与《__hgt》的实质衔接是：half 大于比较要与 >=、无序版本及相反的 <、<= 谓词区分；bfloat16 同名接口还要求先确认操作数类型。
- [__hgtu](_hgtu.md)（`same_topic`）：__hgtu 与 __hgt 都判断 x>y，唯一区别是 unordered 版本在任一 NaN 时返回 true；并读可避免把 NaN 语义误当普通有序比较。
<!-- cannbot:related:end -->
