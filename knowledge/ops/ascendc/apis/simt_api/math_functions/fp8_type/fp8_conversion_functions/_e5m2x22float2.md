---
type: API
title: __e5m2x22float2
description: 将float8_e5m2x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__e5m2x22float2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __e5m2x22float2

功能：将float8_e5m2x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。

函数原型：float2 __e5m2x22float2(const float8_e5m2x2_t x)

参数：x（输入）源操作数。

返回值：将float8_e5m2x2_t类型输入转换成的float2类型数据。特殊值：0→0；-0→-0；nan→nan；inf→inf；-inf→-inf。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__e4m3x22float2](_e4m3x22float2.md)（`related`）：E4M3 与 E5M2 解码的指数/尾数布局不同，按源格式选择。
- [__asc_cvt_float2_to_fp8x2](_asc_cvt_float2_to_fp8x2.md)（`same_topic`）：__e5m2x22float2 与《__asc_cvt_float2_to_fp8x2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [__half22float2](../../half_type/half_precision_conversion_functions/_half22float2.md)（`same_topic`）：__e5m2x22float2 与《__half22float2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [__hif822float2](_hif822float2.md)（`same_topic`）：__e5m2x22float2 与《__hif822float2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [__hif822half2](_hif822half2.md)（`same_topic`）：__e5m2x22float2 与《__hif822half2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [asc_e5m22float (废弃)](../../../../simd_api/c_api/reg/data_type_convert/asc_e5m22float_deprecated.md)（`same_topic`）：__e5m2x22float2 与《asc_e5m22float (废弃)》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [asc_float2e5m2 (废弃)](../../../../simd_api/c_api/reg/data_type_convert/asc_float2e5m2_deprecated.md)（`same_topic`）：《asc_float2e5m2 (废弃)》的任务是“将float类型数据转换为fp8_e5m2类型，支持RINT舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。”。《__e5m2x22float2》具体提供“将float8_e5m2x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。”，它直接用于废弃 float→e5m2 转换的反向转换、舍入饱和和迁移入口。
- [fp8数据类型简介（FP8类型）](../fp8_data_type_intro.md)（`same_topic`）：__e5m2x22float2 与《fp8数据类型简介（FP8类型）》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [fp8数据转换函数](fp8_conversion_functions.md)（`same_topic`）：__e5m2x22float2 与《fp8数据转换函数》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
- [fp8类型](../fp8_type.md)（`same_topic`）：__e5m2x22float2 与《fp8类型》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
