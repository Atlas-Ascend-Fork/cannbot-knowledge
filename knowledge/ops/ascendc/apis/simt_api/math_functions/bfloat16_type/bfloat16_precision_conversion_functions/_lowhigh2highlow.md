---
type: API
title: __lowhigh2highlow
description: 将bfloat16x2_t输入数据的高低16位进行交换，返回交换后的bfloat16x2_t数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__lowhigh2highlow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __lowhigh2highlow

功能：将输入数据的高低16位进行交换并返回。

函数原型：bfloat16x2_t __lowhigh2highlow(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的高低16位进行交换的结果。特殊值：(0, -0)→(-0, 0)；(nan, 正常值)→(正常值, nan)；(inf, -inf)→(-inf, inf)；(ASCRT_MAX_NORMAL_BF16, -ASCRT_MAX_NORMAL_BF16)→(-ASCRT_MAX_NORMAL_BF16, ASCRT_MAX_NORMAL_BF16)；(nan, nan)→(nan, nan)。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
