---
type: API
title: asc_hif82float (废弃)
description: 将hifloat8_t类型数据转换为float类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_hif82float_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_hif82float (废弃)

将hifloat8_t类型数据转换为float类型。

由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、hifloat8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [__hif822float2](../../../../simt_api/math_functions/fp8_type/fp8_conversion_functions/_hif822float2.md)（`related`）：asc_hif82float (废弃) 与《__hif822float2》的实质衔接是：__hif822float2 是现行 SIMT packed 转换，可替代废弃 reg hifloat8→float 路线并保留位宽展开语义。
- [asc_float2hif8 (废弃)](asc_float2hif8_deprecated.md)（`related`）：《asc_hif82float (废弃)》明确“将hifloat8_t类型数据转换为float类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。”；它与《asc_float2hif8 (废弃)》的“将float类型转化为hifloat8_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
