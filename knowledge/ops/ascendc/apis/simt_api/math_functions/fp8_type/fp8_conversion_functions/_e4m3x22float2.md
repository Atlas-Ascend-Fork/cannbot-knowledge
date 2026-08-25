---
type: API
title: __e4m3x22float2
description: 将float8_e4m3x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__e4m3x22float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __e4m3x22float2

功能：将float8_e4m3x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。

函数原型：float2 __e4m3x22float2(const float8_e4m3x2_t x)

参数：x（输入）源操作数。

返回值：将float8_e4m3x2_t类型输入转换成的float2类型数据。特殊值：0→0；-0→-0；nan→nan；448(最大正规值)→448.0。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__asc_cvt_float2_to_fp8x2](_asc_cvt_float2_to_fp8x2.md)（`related`）：通用 float2→FP8x2 转换可选择 E4M3 格式，__e4m3x22float2 是对应的逆向解包；二者构成该格式的量化—反量化验证链。
- [__e5m2x22float2](_e5m2x22float2.md)（`related`）：E4M3 与 E5M2 解码的指数/尾数布局不同，按源格式选择。
- [__hif822float2](_hif822float2.md)（`related`）：HiFloat8 是另一编码格式，不能用 E4M3 解码。
- [asc_float2e4m3 (废弃)](../../../../simd_api/c_api/reg/data_type_convert/asc_float2e4m3_deprecated.md)（`related`）：《__e4m3x22float2》明确“将float8_e4m3x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。”；它与《asc_float2e4m3 (废弃)》的“将float类型转化为fp8_e4m3fn_t类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。”在实际调用参数、数据流或结果校验上直接衔接。
- [fp8数据转换函数](fp8_conversion_functions.md)（`same_topic`）：《__e4m3x22float2》明确“将float8_e4m3x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。”；它与《fp8数据转换函数》的“提供float2、half2与FP8类型（e4m3、e5m2、hifloat8）之间的数据转换函数列表。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
