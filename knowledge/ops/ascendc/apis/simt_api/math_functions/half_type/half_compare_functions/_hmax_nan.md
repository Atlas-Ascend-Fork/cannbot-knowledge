---
type: API
title: __hmax_nan
description: 获取两个输入数据中的最大值。任一输入为nan时结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hmax_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __hmax_nan

功能：获取两个输入数据中的最大值。任一输入为nan时结果为nan。

函数原型：half __hmax_nan(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：两个输入数据中的最大值。特殊值：0→0；0→0；-0→0；-0→-0；inf→inf；-inf→正常值；inf→inf；inf→inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2_nan](../half2_compare_functions/_hmaxx2_nan.md)（`related`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__hmax_nan”明确获取两个输入数据中的最大值。任一输入为nan时结果为nan。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
- [__hmax](_hmax.md)（`same_topic`）：《__hmax_nan》明确“获取两个输入数据中的最大值。任一输入为nan时结果为nan。”；它与《__hmax》的“获取两个输入数据中的最大值。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
