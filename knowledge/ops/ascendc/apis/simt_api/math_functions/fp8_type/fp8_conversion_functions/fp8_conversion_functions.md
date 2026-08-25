---
type: API
title: fp8数据转换函数
description: 提供float2、half2与FP8类型（e4m3、e5m2、hifloat8）之间的数据转换函数列表。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/fp8_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# fp8数据转换函数

提供 float2、half2 与 FP8 类型之间的数据转换，支持 hifloat8（__float22hif82 系列）、e4m3（__e4m3x22float2）和 e5m2（__e5m2x22float2）三种 FP8 编码格式。转换函数提供 rna 和 rh 两种舍入模式，部分带 _sat 后缀的变体支持饱和处理。适用于低精度量化与混合精度计算场景。

<!-- cannbot:related:start -->
## 相关

- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《fp8数据转换函数》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [类型转换函数](../../data_type_conversion/type_conversion_functions/type_conversion_functions.md)（`related`）：FP8 转换需要格式和 SatMode 专用契约，不能沿用普通整数/float 规则。
- [__asc_cvt_float2_to_fp8x2](_asc_cvt_float2_to_fp8x2.md)（`same_topic`）：《__asc_cvt_float2_to_fp8x2》明确“将float2的两个分量按CAST_RINT模式转换为FP8类型（e4m3或e5m2）的8位浮点数，支持饱和与非饱和溢出处理，结果以位级打包存储。”；它与《fp8数据转换函数》的“提供float2、half2与FP8类型（e4m3、e5m2、hifloat8）之间的数据转换函数列表。”在实际调用参数、数据流或结果校验上直接衔接。
- [__e4m3x22float2](_e4m3x22float2.md)（`same_topic`）：《__e4m3x22float2》明确“将float8_e4m3x2_t类型数据的两个分量转换为浮点数，返回转换后的float2类型数据。”；它与《fp8数据转换函数》的“提供float2、half2与FP8类型（e4m3、e5m2、hifloat8）之间的数据转换函数列表。”在实际调用参数、数据流或结果校验上直接衔接。
- [__e5m2x22float2](_e5m2x22float2.md)（`same_topic`）：__e5m2x22float2 与《fp8数据转换函数》的实质衔接是：该接口把 packed E5M2 两 lane 解码成 float2；E4M3/HIF8/half2 解码、FP8 类型说明和反向编码入口共同限定格式选择与 round/saturation。
<!-- cannbot:related:end -->
