---
type: API
title: __half22hif82_rh
description: 将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/fp8_type/fp8_conversion_functions/__half22hif82_rh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half22hif82_rh

功能：将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。

函数原型：hifloat8x2_t __half22hif82_rh(const half2 x)

参数：x（输入）源操作数。

返回值：将输入的两个分量遵循CAST_HYBRID模式转换成的hifloat8x2_t类型数据。本接口受全局饱和模式影响，。特殊值：±0→0；nan→0；inf→hif8 最大有限值；-inf→-hif8 最大有限值；(超出 hif8 范围的 half 有限值,±inf)→±hif8 最大有限值。

约束：SIMT编程场景当前不支持使用该接口。需包含头文件 simt_api/asc_fp8.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hif822half2](_hif822half2.md)（`related`）：__half22hif82_rh 是 half2 到 hifloat8x2 的正向窄化，__hif822half2 是反向扩展；共同给出 round-trip 类型通路和特殊值不可逆边界。
- [AscHalf2Hif8](../../../../simd_api/c_api/reg/data_type_convert/asc_half2hif8.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rh》明确“将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rh_sat](_half22hif82_rh_sat.md)（`same_topic`）：__half22hif82_rh 的核心契约是“将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据”；__half22hif82_rh_sat 补充“饱和模式下，将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据”。
- [__half22hif82_rna](_half22hif82_rna.md)（`same_topic`）：__half22hif82_rh 与 __half22hif82_rna 都把 half2 转为 hifloat8x2；两者只在 HYBRID 与 ROUND 模式及其特殊值处理上不同。
- [__half22hif82_rna_sat](_half22hif82_rna_sat.md)（`same_topic`）：__half22hif82_rh 的核心契约是“将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据”；__half22hif82_rna_sat 补充“饱和模式下，将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据”。
<!-- cannbot:related:end -->
