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

- [__hequ](_hequ.md)（`related`）：功能：比较两个half类型数据是否相等，相等时返回true。若任一输入为nan，返回true。；返回值：比较输入数据是否相等的结果，饱和与非饱和模式行为一致。特殊值：x=y，均为非nan的有限值→true；x≠y，均为非nan的有限值→false；±0→true；inf→true；-inf→true；inf→false；任一操作数为nan→false。。两接口都比较 half 相等性，但 _hequ 对任一 NaN 返回 true，而 _heq 明确返回 false；并读可直接完成有序与无序比较的语义选型。
<!-- cannbot:related:end -->
