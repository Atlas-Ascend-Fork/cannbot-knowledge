---
type: API
title: __float2half_rn_sat
description: 饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half_rn_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2half_rn_sat

功能：饱和模式下，将浮点数转换为半精度浮点数，并遵循CAST_RINT模式，返回转换后的值。

函数原型：half __float2half_rn_sat(const float x)

参数：x（输入）源操作数。

返回值：将输入遵循CAST_RINT模式转换成的半精度浮点数。特殊值：±0→±0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。
