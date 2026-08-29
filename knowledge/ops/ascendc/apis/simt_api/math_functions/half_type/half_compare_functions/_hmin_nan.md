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

- [__hmin](_hmin.md)（`same_topic`）：返回值：两个输入数据中的最小值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→normal；nan→nan；-inf→-inf；(normal,-inf)→-inf；inf→normal；(normal,inf)→normal。；返回值：两个输入数据中的最小值。特殊值：-0→x；(+0,-0)→y；nan→nan；(任意值,nan)→nan；-inf→-inf；(任意值,-inf)→-inf；inf→y。。两接口均求 half 标量最小值，但 __hmin_nan 明确传播任一 NaN，而 __hmin 的特殊值结果受全局饱和寄存器及操作数组合影响。
<!-- cannbot:related:end -->
