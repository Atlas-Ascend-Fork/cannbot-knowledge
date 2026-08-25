---
type: API
title: __float22hif82_rh_sat
description: 饱和模式下，将float2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__float22hif82_rh_sat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22hif82_rh_sat

功能：饱和模式下，将float2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __float22hif82_rh_sat(const float2 x)

参数：x（输入）源操作数。

返回值：饱和模式下将输入的两个分量遵循CAST_HYBRID模式转换成的hifloat8x2_t类型数据。特殊值：±0→0；nan→0；inf→32768；-inf→-32768。

约束：使用此接口前需将CTRL[60]寄存器设置为0，否则饱和模式不生效。设置方式请参见控制饱和行为的方式。 SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__float22hif82_rh_sat》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [__hif822float2](_hif822float2.md)（`related`）：反向解码用于 round-trip 验证。
- [__float22hif82_rh](_float22hif82_rh.md)（`same_topic`）：rh 与 rh_sat 共享 CAST_HYBRID 舍入，sat 版用于显式饱和语义，是同一 HiFloat8x2 转换的直接对照。
- [__float22hif82_rna_sat](_float22hif82_rna_sat.md)（`same_topic`）：RNA 改变 tie 舍入规则。
<!-- cannbot:related:end -->
