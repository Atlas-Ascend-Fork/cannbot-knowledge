---
type: API
title: AscHalf2Hif8
description: 将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2hif8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscHalf2Hif8

将half类型转化为hifloat8_t类型，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、hifloat8_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 当数据写入目的操作数索引为奇数的位置，索引为偶数位置的数值置零。反之亦然。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [舍入模式与饱和模式](rounding_mode.md)（`related`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《舍入模式与饱和模式》明确“在进行数据类型转换时，Ascend C API支持多种舍入模式和饱和模式。这些模式决定了当源数据类型转换为不同精度或范围的目标数据类型时，如何处理数值的舍入和溢出问题。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [AscHif82Half](asc_hif82half.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《AscHif82Half》明确“将src中hifloat8_t数据类型的元素转换为half数据类型，并将结果写入dst。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rh](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_half22hif82_rh.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rh》明确“将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rh_sat](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_half22hif82_rh_sat.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rh_sat》明确“饱和模式下，将half2类型数据的两个分量遵循CAST_HYBRID模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rna](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_half22hif82_rna.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rna》明确“将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__half22hif82_rna_sat](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_half22hif82_rna_sat.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__half22hif82_rna_sat》明确“饱和模式下，将half2类型数据的两个分量遵循CAST_ROUND模式转换为hifloat8_t精度，返回转换后的hifloat8x2_t类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
- [__hif822half2](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_hif822half2.md)（`same_topic`）：《AscHalf2Hif8》处理“将half类型转化为hifloat8_t类型，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为2:1。”。《__hif822half2》明确“将hifloat8x2_t类型数据的两个分量转换为半精度浮点数，返回转换后的half2类型数据。”，可直接用于核对packed half2 与 hif8x2 的双向转换、舍入和饱和模式合同。
<!-- cannbot:related:end -->
