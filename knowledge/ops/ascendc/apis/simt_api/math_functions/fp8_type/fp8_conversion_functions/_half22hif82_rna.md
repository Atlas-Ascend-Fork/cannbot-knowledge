---
type: API
title: __half22hif82_rna
description: 将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__half22hif82_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half22hif82_rna

功能：将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __half22hif82_rna(const half2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_ROUND模式转换成的hifloat8x2_t类型数据。本接口受全局饱和模式影响，。特殊值：±0→0；nan→+0；inf→32768；-inf→-32768；ASCRT_MAX_NORMAL_FP16→32768；-ASCRT_MAX_NORMAL_FP16→-32768；ASCRT_MIN_DENORM_FP16→0。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__half22hif82_rna》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [__hif822half2](_hif822half2.md)（`related`）：反向 __hif822half2 可构造 half2→HiFloat8x2→half2 往返探针，量化误差和特殊值映射可直接观测。
- [AscHalf2Hif8](../../../../simd_api/c_api/reg/data_type_convert/asc_half2hif8.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rna》明确“将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rh](_half22hif82_rh.md)（`same_topic`）：__half22hif82_rh 与 __half22hif82_rna 都把 half2 转为 hifloat8x2；两者只在 HYBRID 与 ROUND 模式及其特殊值处理上不同。
- [__half22hif82_rna_sat](_half22hif82_rna_sat.md)（`same_topic`）：《__half22hif82_rna》明确“将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”；它与《__half22hif82_rna_sat》的“饱和模式下，将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
