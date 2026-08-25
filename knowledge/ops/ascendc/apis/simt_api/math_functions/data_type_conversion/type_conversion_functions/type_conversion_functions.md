---
type: API
title: 类型转换函数
description: 提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/type_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 类型转换函数

提供 float 与 int、uint、ll、ull 等整型之间的双向类型转换，支持 rn、rz、rd、ru、rna 五种舍入模式。还包含 __float_as_int、__float_as_uint、__int_as_float、__uint_as_float 等位级重新解释函数，在不改变底层比特表示的前提下完成类型映射。适用于 SIMT 编程模型下的精确类型控制场景。

<!-- cannbot:related:start -->
## 相关

- [__float2float_ru](_float2float_ru.md)（`related`）：__float2float_ru 与《类型转换函数》的实质衔接是：__float2float_ru 对 float 做向上取整；RN/RD/RNA/RZ 变体、类型转换总览和 AscFloat2float 直接对照五种舍入方向与特殊值。
- [__float2int_rn](_float2int_rn.md)（`related`）：__float2int_rn 与《类型转换函数》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rz](_float2int_rz.md)（`related`）：__float2int_rz 与《类型转换函数》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
- [__float2ll_rna](_float2ll_rna.md)（`related`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2uint_rd](_float2uint_rd.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_rna](_float2uint_rna.md)（`related`）：__float2uint_rna 与《类型转换函数》的实质衔接是：__float2uint_rna 与 RN/RD/RU/RZ 变体保持 float→uint32 目标不变而替换舍入规则；signed int 和反向 uint→float RNA 说明符号/方向边界，类型转换总览统一特殊值契约。
- [__float_as_uint](_float_as_uint.md)（`related`）：bit reinterpret 与数值转换不同；总览用于区分两类入口。
- [bfloat16类型精度转换函数](../../bfloat16_type/bfloat16_precision_conversion_functions/bfloat16_precision_conversion_functions.md)（`related`）：bfloat16类型精度转换函数 与《类型转换函数》的实质衔接是：该页概括 bfloat16 与 float/half/整数的双向转换及五种舍入，通用类型转换页和精度舍入规则补充模式语义，half 转换页提供同一转换矩阵在另一低精度类型上的对照。
- [fp8数据转换函数](../../fp8_type/fp8_conversion_functions/fp8_conversion_functions.md)（`related`）：FP8 转换需要格式和 SatMode 专用契约，不能沿用普通整数/float 规则。
- [half类型精度转换函数](../../half_type/half_precision_conversion_functions/half_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
- [数据类型转换](../data_type_conversion.md)（`related`）：类型转换函数页把 overview 的规则映射到 float/int/uint/ll/ull 各舍入模式的显式函数，是从规则到具体调用的入口。
- [精度转换（数据结构）](../../../../simd_api/basic_api/data_structures/precision_conversion.md)（`related`）：精度转换（数据结构） 与《类型转换函数》的实质衔接是：本卡给出跨类型舍入、饱和与尾数损失规则；SIMT、Memory/Reg Cast 总览和具体 f32→s64 失败分别把这些规则落实到模式选择、数据宽度与编译约束。
<!-- cannbot:related:end -->
