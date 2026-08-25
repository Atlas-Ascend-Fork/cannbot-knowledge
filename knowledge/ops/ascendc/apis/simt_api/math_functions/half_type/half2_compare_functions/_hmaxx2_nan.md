---
type: API
title: __hmaxx2_nan
description: 获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hmaxx2_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmaxx2_nan

功能：获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。

函数原型：half2 __hmaxx2_nan(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最大值。特殊值：±0→0；x或y为nan→nan；x或y为inf→inf；-inf→有限值；(有限值,-inf)→有限值；x=y=-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
