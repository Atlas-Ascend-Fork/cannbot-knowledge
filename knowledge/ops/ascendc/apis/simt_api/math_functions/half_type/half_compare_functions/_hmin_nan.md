---
type: API
title: __hmin_nan
description: 获取两个输入数据中的最小值。任一输入为nan时结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hmin_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __hmin_nan

功能：获取两个输入数据中的最小值。任一输入为nan时结果为nan。

函数原型：half __hmin_nan(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：两个输入数据中的最小值。特殊值：-0→x；(+0,-0)→y；nan→nan；(任意值,nan)→nan；-inf→-inf；(任意值,-inf)→-inf；inf→y。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmin](_hmin.md)（`same_topic`）：《__hmin》明确“获取两个输入数据中的最小值。”；它与《__hmin_nan》的“获取两个输入数据中的最小值。任一输入为nan时结果为nan。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
