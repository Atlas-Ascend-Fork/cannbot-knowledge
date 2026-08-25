---
type: API
title: __half22hif82_rh_sat
description: 饱和模式下，将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__half22hif82_rh_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half22hif82_rh_sat

功能：饱和模式下，将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __half22hif82_rh_sat(const half2 x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入的两个分量遵循CAST_HYBRID模式转换成的hifloat8x2_t类型数据。特殊值：±0→0；nan→0；inf→32768；-inf→-32768；ASCRT_MAX_NORMAL_FP16→32768；-ASCRT_MAX_NORMAL_FP16→-32768。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
