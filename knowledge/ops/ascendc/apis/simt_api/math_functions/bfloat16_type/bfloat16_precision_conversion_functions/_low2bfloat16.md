---
type: API
title: __low2bfloat16
description: 从bfloat16x2_t类型输入数据中提取低16位，作为bfloat16_t类型返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__low2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __low2bfloat16

功能：返回输入数据的低16位。

函数原型：bfloat16_t __low2bfloat16(const bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据的低16位。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf；ASCRT_MAX_NORMAL_BF16→ASCRT_MAX_NORMAL_BF16；-ASCRT_MAX_NORMAL_BF16→-ASCRT_MAX_NORMAL_BF16。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
