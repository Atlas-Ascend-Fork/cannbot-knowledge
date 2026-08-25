---
type: API
title: __float22hif82_rna
description: 将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__float22hif82_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float22hif82_rna

功能：将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __float22hif82_rna(const float2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_ROUND模式转换成的hifloat8x2_t类型数据。本接口受全局饱和模式影响，。特殊值：±0→0；nan→0；inf→32768；-inf→-32768。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [HiFloat8 SatMode::SAT Cast NaN 映射 0x00](../../../../../runbooks/precision/hifloat8_satmode_sat_cast_nan_0x00.md)（`exemplifies`）：该精度卡用全 NaN 输入确认 HiFloat8 SAT 路径映射为 0x00，直接给出选择非 sat/sat 转换接口时的字节级 oracle。
- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`related`）：__half22hif82_rh_sat 与《__float22hif82_rna》的实质衔接是：half2→hif8x2 的 hybrid 舍入+饱和转换与非饱和、RNA、float2 入口、反向转换及 NaN 饱和故障共享编码契约。
- [asc_float2hif8 (废弃)](../../../../simd_api/c_api/reg/data_type_convert/asc_float2hif8_deprecated.md)（`related`）：《__float22hif82_rna》明确“将float2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”；它与《asc_float2hif8 (废弃)》的“将float类型转化为hifloat8_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。”在实际调用参数、数据流或结果校验上直接衔接。
- [__float22hif82_rna_sat](_float22hif82_rna_sat.md)（`same_topic`）：两接口都按 RNA 将 float2 转为 hifloat8x2，sat 版本仅改变饱和及特殊值映射，可逐字节对照转换结果。
<!-- cannbot:related:end -->
