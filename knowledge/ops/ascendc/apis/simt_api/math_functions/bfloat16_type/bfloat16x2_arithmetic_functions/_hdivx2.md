---
type: API
title: __hdivx2
description: 计算两个bfloat16x2_t类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_arithmetic_functions/__hdivx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hdivx2

功能：计算两个bfloat16x2_t类型数据各分量的相除结果，并遵循CAST_RINT模式对结果进行舍入。

函数原型：bfloat16x2_t __hdivx2(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量相除的结果。相除的分量x和y满足。特殊值：(±0,±0,nan)→0；(±inf,±inf,nan)→0；(x，y任意一个为nan,nan)→0；(±inf,±0,±inf)→±ASCRT_MAX_NORMAL_BF16。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
