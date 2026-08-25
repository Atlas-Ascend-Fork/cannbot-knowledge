---
type: API
title: __hmaxx2_nan
description: 获取两个bfloat16x2_t类型数据各分量的最大值。任一分量为nan时，对应分量的计算结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hmaxx2_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmaxx2_nan

功能：获取两个bfloat16x2_t类型数据各分量的最大值。任一分量为nan时，对应分量的计算结果为nan。

函数原型：bfloat16x2_t __hmaxx2_nan(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最大值。比较的分量x和y特殊值满足。特殊值：任一分量含nan→nan；inf→inf；(任意值,inf)→inf；inf→inf；-inf→y；(任意值,-inf)→x；0→0；-0→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2](_hmaxx2.md)（`same_topic`）：《__hmaxx2_nan》明确“获取两个bfloat16x2_t类型数据各分量的最大值。任一分量为nan时，对应分量的计算结果为nan。”；它与《__hmaxx2》的“获取两个bfloat16x2_t类型数据各分量的最大值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
