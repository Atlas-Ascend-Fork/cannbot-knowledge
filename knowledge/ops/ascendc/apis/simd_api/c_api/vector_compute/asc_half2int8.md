---
type: API
title: AscHalf2int8
description: 将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入
  - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_half2int8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscHalf2int8

将half类型转化为int8_t类型，并支持多种舍入模式。
函数原型：void asc_half2int8(__ubuf__ int8_t* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [__half2int_rd](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rd.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rd》明确提供“遵循CAST_FLOOR模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__half2int_rn](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rn.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rn》明确提供“遵循CAST_RINT模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__half2int_rna](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rna.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rna》明确提供“遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__half2int_ru](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_ru.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_ru》明确提供“遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [__half2int_rz](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rz.md)（`related`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rz》明确提供“遵循CAST_TRUNC模式，将half类型数据转换为int类型数据，返回转换后的值。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [AscHalf2Int8](../reg/data_type_convert/asc_half2int8.md)（`same_topic`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《AscHalf2Int8》明确提供“将half类型转化为int8_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [AscMulCastHalf2int8](asc_mul_cast_half2int8.md)（`same_topic`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《AscMulCastHalf2int8》明确提供“按元素求积，并将结果转换为int8_t类型。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
<!-- cannbot:related:end -->
