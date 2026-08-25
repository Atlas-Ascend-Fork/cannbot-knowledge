---
type: API
title: 精度转换（数据结构）
description: 在了解不同类型之间的精度转换规则之前，需先了解二进制的精度舍入规则。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/precision_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 精度转换（数据结构）

不同数据类型间精度转换的舍入规则和溢出处理。源值超出目标类型表示范围时溢出，默认按饱和模式处理。主要转换路径：int4b_t→int16_t/half/bfloat16_t（无精度损失）；int8_t/uint8_t→half/float（无精度损失）；half→float（无精度损失）；float→half（CAST_RINT 舍入模式，尾数 23→10bits）；float→bfloat16_t（截断尾数 23→7bits）；float→int8_t/int4b_t（CAST_RINT 后饱和截断）；int32_t→half（反量化 DEQF16/REQ8 等，带量化参数）。

Cast 接口支持 RINT/CAST_RINT/CAST_NONE 等舍入模式。950 的 float32 尾数为 10bits，golden 数据生成需将量化参数低 13bits 清零。

<!-- cannbot:related:start -->
## 相关

- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../../../../runbooks/compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`exemplifies`）：精度转换（数据结构） 与《f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
- [bfloat16类型精度转换函数](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/bfloat16_precision_conversion_functions.md)（`related`）：bfloat16类型精度转换函数 与《精度转换（数据结构）》的实质衔接是：该页概括 bfloat16 与 float/half/整数的双向转换及五种舍入，通用类型转换页和精度舍入规则补充模式语义，half 转换页提供同一转换矩阵在另一低精度类型上的对照。
- [half类型精度转换函数](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/half_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《精度转换（数据结构）》说明在了解不同类型之间的精度转换规则之前，需先了解二进制的精度舍入规则。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [内置数据类型（数据结构）](builtin_data_types.md)（`related`）：精度转换（数据结构） 与《内置数据类型（数据结构）》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
- [类型转换](../memory_vector_compute/type_conversion/type_conversion.md)（`related`）：精度转换（数据结构） 与《类型转换》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
- [类型转换](../reg_vector_compute/type_conversion/type_conversion.md)（`related`）：精度转换（数据结构） 与《类型转换》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
- [类型转换函数](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/type_conversion_functions.md)（`related`）：精度转换（数据结构） 与《类型转换函数》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
<!-- cannbot:related:end -->
