---
type: API
title: __half2int_rna
description: 遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2int_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2int_rna

功能：遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。

函数原型：int __half2int_rna(const half x)

参数：x（输入）源操作数。

返回值：遵循CAST_ROUND模式，将half类型数据转换为int类型数据。特殊值：±0→0；nan→0；inf→2147483647（int32_t最大值）；-inf→-2147483648（int32_t最小值）；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；0.5→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int16](../../../../simd_api/c_api/vector_compute/asc_half2int16.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rna》具体提供“遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [AscHalf2int8](../../../../simd_api/c_api/vector_compute/asc_half2int8.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rna》明确提供“遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__bfloat162int_rna](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rna.md)（`related`）：bfloat16 源版本目标与舍入一致，但源精度和范围不同，适合 dtype 迁移对照。
- [__half2int_rd](_half2int_rd.md)（`same_topic`）：__half2int_rd 与《__half2int_rna》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
- [__half2int_rn](_half2int_rn.md)（`same_topic`）：两卡都是 half→int，rn 使用 nearest-even，rna 在中点远离零。
- [__half2int_ru](_half2int_ru.md)（`same_topic`）：__half2int_ru 与《__half2int_rna》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2int_rz](_half2int_rz.md)（`same_topic`）：两卡同为 half→int，分别 toward-zero 与 ties-away。
<!-- cannbot:related:end -->
