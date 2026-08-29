---
type: API
title: __float22half2_rna_sat
description: 将float2类型数据的两个分量遵循CAST_ROUND模式转换为半精度浮点数，返回转换后的half2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float22half2_rna_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22half2_rna_sat

功能：将float2类型数据的两个分量遵循CAST_ROUND模式转换为半精度浮点数，返回转换后的half2类型数据。

函数原型：half2 __float22half2_rna_sat(const float2 x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入的两个分量遵循CAST_ROUND模式转换成的half2类型数据。本接口受全局饱和寄存器的影响，。特殊值：±0→0；-0→-0；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景由于无法设置CTRL寄存器，本接口的饱和模式不生效。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float22half2_rna](_float22half2_rna.md)（`same_topic`）：函数原型：half2 __float22half2_rna(const float2 x)；函数原型：half2 __float22half2_rna_sat(const float2 x)。两接口都执行 float2 到 half2 的 rna 转换，右侧只改变为饱和输出，是同一双元素精度转换的模式变体。
<!-- cannbot:related:end -->
