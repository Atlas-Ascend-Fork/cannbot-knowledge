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

<!-- cannbot:related:start -->
## 相关

- [__half22hif82_rh](_half22hif82_rh.md)（`related`）：__half22hif82_rh 是 half2 到 hifloat8x2 的正向窄化，__hif822half2 是反向扩展；共同给出 round-trip 类型通路和特殊值不可逆边界。
- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__hif822half2》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [__half22hif82_rna](_half22hif82_rna.md)（`related`）：反向 __hif822half2 可构造 half2→HiFloat8x2→half2 往返探针，量化误差和特殊值映射可直接观测。
- [AscHalf2Hif8](../../../../simd_api/c_api/reg/data_type_convert/asc_half2hif8.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__hif822half2》明确“将hifloat8x2_t类型数据的两个分量转换为半精度浮点数，返回转换后的half2类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__e5m2x22float2](_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《__hif822half2》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
