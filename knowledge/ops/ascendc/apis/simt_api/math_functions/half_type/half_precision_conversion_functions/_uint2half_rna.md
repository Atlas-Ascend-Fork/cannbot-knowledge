---
type: API
title: __uint2half_rna
description: 遵循CAST_ROUND模式，将uint32类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__uint2half_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __uint2half_rna

功能：遵循CAST_ROUND模式，将uint32类型数据转换为half类型数据，返回转换后的值。

函数原型：half __uint2half_rna(const unsigned int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的half类型数据。特殊值：0→0；2049→2050；4098→4100；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；65505→ASCRT_MAX_NORMAL_FP16；65520（溢出中点）→inf；4294967295（uint32_t最大值）→inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
