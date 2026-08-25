---
type: API
title: __hdiv
description: 计算两个half类型数据相除的结果，并遵循CAST_RINT模式对结果进行舍入处理。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_arithmetic_functions/__hdiv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hdiv

功能：计算两个half类型数据相除的结果，并遵循CAST_RINT模式对结果进行舍入处理。

函数原型：half __hdiv(const half x, const half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据相除的结果。特殊值：(±0,±0,nan)→0；(±inf,±inf,nan)→0；(x，y任意一个为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
