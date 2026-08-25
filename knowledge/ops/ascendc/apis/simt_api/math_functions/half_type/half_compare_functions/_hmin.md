---
type: API
title: __hmin
description: 获取两个输入数据中的最小值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hmin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# __hmin

功能：获取两个输入数据中的最小值。

函数原型：half __hmin(half x, half y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：两个输入数据中的最小值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→normal；nan→nan；-inf→-inf；(normal,-inf)→-inf；inf→normal；(normal,inf)→normal。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
