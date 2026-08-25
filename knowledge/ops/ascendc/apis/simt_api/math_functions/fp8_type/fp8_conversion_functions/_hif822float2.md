---
type: API
title: __hif822float2
description: 将hifloat8x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__hif822float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __hif822float2

功能：将hifloat8x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。

函数原型：float2 __hif822float2(const hifloat8x2_t x)

参数：x（输入）源操作数。

返回值：将hifloat8x2_t类型输入转换成的float2类型数据。特殊值：0→0；nan→nan；inf→inf；-inf→-inf。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__e4m3x22float2](_e4m3x22float2.md)（`related`）：HiFloat8 是另一编码格式，不能用 E4M3 解码。
- [__float22hif82_rh_sat](_float22hif82_rh_sat.md)（`related`）：反向解码用于 round-trip 验证。
- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__hif822float2》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [asc_hif82float (废弃)](../../../../simd_api/c_api/reg/data_type_convert/asc_hif82float_deprecated.md)（`related`）：asc_hif82float (废弃) 与《__hif822float2》的实质衔接是：__hif822float2 是现行 SIMT packed 转换，可替代废弃 reg hifloat8→float 路线并保留位宽展开语义。
- [__e5m2x22float2](_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《__hif822float2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
