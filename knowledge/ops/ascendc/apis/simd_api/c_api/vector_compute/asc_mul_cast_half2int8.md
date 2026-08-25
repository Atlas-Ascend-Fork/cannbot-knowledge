---
type: API
title: AscMulCastHalf2int8
description: 按元素求积，并将结果转换为int8_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul_cast_half2int8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscMulCastHalf2int8

按元素求积，并将结果转换为int8_t类型。计算公式如下： 精度转换规则：将源操作数的乘积按照RINT舍入模式（四舍六入五成双舍入），溢出做饱和处理。
函数原型：void asc_mul_cast_half2int8(__ubuf__ int8_t* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Int8](../reg/data_type_convert/asc_half2int8.md)（`same_topic`）：AscMulCastHalf2int8 与《AscHalf2Int8》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [AscHalf2int8](asc_half2int8.md)（`same_topic`）：《AscHalf2int8》处理“将half类型转化为int8_t类型，并支持多种舍入模式。 - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。《AscMulCastHalf2int8》明确提供“按元素求积，并将结果转换为int8_t类型。”，其参数、调用或验证步骤直接接入half 到 int8 的同源同目标转换和 rounding/saturation 模式。
- [AscMul](asc_mul.md)（`same_topic`）：AscMulCastHalf2int8 与《AscMul》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [AscMulCastHalf2uint8](asc_mul_cast_half2uint8.md)（`same_topic`）：AscMulCastHalf2int8 与《AscMulCastHalf2uint8》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [MulCast](../../basic_api/memory_vector_compute/composite_compute/mul_cast.md)（`same_topic`）：AscMulCastHalf2int8 与《MulCast》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [Rint](../../adv_api/math_compute/rint_interface/rint.md)（`same_topic`）：AscMulCastHalf2int8 与《Rint》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
- [__half2int_rn](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rn.md)（`same_topic`）：AscMulCastHalf2int8 与《__half2int_rn》的实质衔接是：AscMulCastHalf2int8 融合 half 乘法、RINT 和 int8 饱和；MulCast、纯 Mul、Half2Int8 与 Rint 入口分别核对融合、目标宽度和舍入。
<!-- cannbot:related:end -->
