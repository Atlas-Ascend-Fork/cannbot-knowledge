---
type: API
title: __hminx2
description: 获取两个half2类型数据各分量的最小值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hminx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hminx2

功能：获取两个half2类型数据各分量的最小值。

函数原型：half2 __hminx2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最小值。特殊值：(0,-0,-0)→-0；(-0,0,-0)→-0；(-0,-0,-0)→-0；(0,0,0)→0；(nan,nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
