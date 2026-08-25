---
type: API
title: __hif822half2
description: 将hifloat8x2_t类型数据的两个分量转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__hif822half2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __hif822half2

功能：将hifloat8x2_t类型数据的两个分量转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __hif822half2(const hifloat8x2_t x)

参数：x（输入）源操作数。

返回值：将hifloat8x2_t类型输入转换成的half2类型数据。特殊值：±0→0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
