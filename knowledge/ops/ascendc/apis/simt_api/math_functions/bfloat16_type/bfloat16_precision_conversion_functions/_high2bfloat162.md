---
type: API
title: __high2bfloat162
description: 将bfloat16x2_t输入数据的高16位填充到bfloat16x2_t的前后两个分量，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__high2bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __high2bfloat162

功能：将输入数据的高16位填充到bfloat16x2并返回结果。

函数原型：bfloat16x2_t __high2bfloat162(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的高16位填充到bfloat16x2的结果。特殊值：0→(0, 0)；-0→(-0, -0)；nan→(nan, nan)；inf→(inf, inf)；-inf→(-inf, -inf)。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
