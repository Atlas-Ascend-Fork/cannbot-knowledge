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

- [__hge](_hge.md)（`related`）：返回值：比较输入的第一个数是否大于或等于第二个数的结果。任一输入为nan时，返回false。；返回值：比较输入的第一个数是否大于或等于第二个数的结果。特殊值：x<y→false；x>y→true；x=y→true；任一值为nan→true；±0→true；inf→true；-inf→false。。两接口对普通 half 的大于等于判断相同，差异集中在 ordered 与 unordered 的 NaN 处理，属于直接的比较谓词选型关系。
<!-- cannbot:related:end -->
