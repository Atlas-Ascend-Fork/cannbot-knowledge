---
type: API
title: __half2int_ru
description: 遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2int_ru.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __half2int_ru

功能：遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。

函数原型：int __half2int_ru(const half x)

参数：x（输入）源操作数。

返回值：遵循CAST_CEIL模式，将half类型数据转换为int类型数据。特殊值：±0→0；nan→0；inf→2147483647（int32_t最大值）；-inf→-2147483648（int32_t最小值）；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；0.5→1；-0.5→-1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int16](../../../../simd_api/c_api/vector_compute/asc_half2int16.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_ru》具体提供“遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [AscHalf2int8](../../../../simd_api/c_api/vector_compute/asc_half2int8.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_ru》明确提供“遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__half2ll_ru](_half2ll_ru.md)（`related`）：__half2int_ru 与《__half2ll_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2ull_ru](_half2ull_ru.md)（`related`）：__half2int_ru 与《__half2ull_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [AscHalf2Int16](../../../../simd_api/c_api/reg/data_type_convert/asc_half2int16.md)（`same_topic`）：__half2int_ru 与《AscHalf2Int16》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [AscHalf2Int32](../../../../simd_api/c_api/reg/data_type_convert/asc_half2int32.md)（`same_topic`）：__half2int_ru 与《AscHalf2Int32》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [AscHalf2int32](../../../../simd_api/c_api/vector_compute/asc_half2int32.md)（`same_topic`）：__half2int_ru 与《AscHalf2int32》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__bfloat162int_ru](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_ru.md)（`same_topic`）：__half2int_ru 与《__bfloat162int_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__float2int_ru](../../data_type_conversion/type_conversion_functions/_float2int_ru.md)（`same_topic`）：__half2int_ru 与《__float2int_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2int_rd](_half2int_rd.md)（`same_topic`）：__half2int_ru 与《__half2int_rd》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2int_rn](_half2int_rn.md)（`same_topic`）：__half2int_ru 与《__half2int_rn》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2int_rna](_half2int_rna.md)（`same_topic`）：__half2int_ru 与《__half2int_rna》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2int_rz](_half2int_rz.md)（`same_topic`）：__half2int_ru 与《__half2int_rz》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
- [__half2uint_ru](_half2uint_ru.md)（`same_topic`）：__half2int_ru 与《__half2uint_ru》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
<!-- cannbot:related:end -->
