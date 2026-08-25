---
type: API
title: AscHalf2int16
description: 将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入
  - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_half2int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscHalf2int16

将half类型数据转换为int16_t，并支持多种舍入模式。
函数原型：void asc_half2int16_rn(__ubuf__ int16_t* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2int16](asc_float2int16.md)（`related`）：half 源版本精度/范围不同。
- [__half2int_rd](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rd.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rd》具体提供“遵循CAST_FLOOR模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [__half2int_rn](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rn.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rn》具体提供“遵循CAST_RINT模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [__half2int_rna](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rna.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rna》具体提供“遵循CAST_ROUND模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [__half2int_ru](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_ru.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_ru》具体提供“遵循CAST_CEIL模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [__half2int_rz](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rz.md)（`related`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《__half2int_rz》具体提供“遵循CAST_TRUNC模式，将half类型数据转换为int类型数据，返回转换后的值。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
- [AscHalf2Int16](../reg/data_type_convert/asc_half2int16.md)（`same_topic`）：《AscHalf2int16》的任务是“将half类型数据转换为int16_t，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《AscHalf2Int16》具体提供“将half类型数据转换为int16_t，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。”，它直接用于half→int16 的同源同目标实现及五种舍入模式。
<!-- cannbot:related:end -->
