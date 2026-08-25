---
type: API
title: __habsx2
description: 计算输入bfloat16x2_t类型数据各分量的绝对值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__habsx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __habsx2

功能：计算输入bfloat16x2_t类型数据各分量的绝对值。

函数原型：bfloat16x2_t __habsx2(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各分量的绝对值。特殊值：±0→0；nan→nan；±inf→inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
