---
type: API
title: __hmulx2
description: 计算两个bfloat16x2_t类型数据各分量的相乘结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hmulx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmulx2

功能：计算两个bfloat16x2_t类型数据各分量的相乘结果，并遵循CAST_RINT模式对结果进行舍入。

函数原型：bfloat16x2_t __hmulx2(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量相乘的结果。相乘的分量x和y满足。特殊值：±0→±0（符号由x和y符号异或决定）；±0→nan；±inf→nan；±inf→±inf（符号由x和y符号异或决定）；x，y任意一个为nan→nan；ASCRT_MAX_NORMAL_BF16→inf；-ASCRT_MAX_NORMAL_BF16→-inf。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
