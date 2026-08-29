---
type: API
title: __lows2bfloat162
description: 分别提取两个bfloat162输入的低16位，并填充到bfloat162中，返回填充后的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__lows2bfloat162.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __lows2bfloat162

功能：分别提取两个bfloat162输入的低16位，并填充到bfloat162中，返回填充后的数据。

函数原型：bfloat16x2_t __lows2bfloat162(const bfloat16x2_t x, const bfloat16x2_t y)

参数：x（输入）源操作数。

返回值：分别提取两个bfloat162输入的低16位，并填充到bfloat162的结果。特殊值：0→(0, 0)；-0→(-0, -0)；0→(0, -0)；-0→(-0, 0)；nan→(nan, 正常值)；(正常值,nan)→(正常值, nan)；nan→(nan, nan)。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
