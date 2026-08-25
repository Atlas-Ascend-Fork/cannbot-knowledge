---
type: API
title: __int2bfloat16_rna
description: 遵循CAST_ROUND模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__int2bfloat16_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __int2bfloat16_rna

功能：遵循CAST_ROUND模式，将int32类型数据转换为bfloat16类型数据，返回转换后的值。

函数原型：bfloat16_t __int2bfloat16_rna(const int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的bfloat16类型数据。特殊值：2147483647（INT32_MAX）→2147483648；-2147483648（INT32_MIN）→-2147483648（INT32_MIN）；257→258；-257→-258。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
