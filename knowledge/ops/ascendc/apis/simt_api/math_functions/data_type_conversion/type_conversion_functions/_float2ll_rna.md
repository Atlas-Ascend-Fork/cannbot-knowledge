---
type: API
title: __float2ll_rna
description: 遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2ll_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2ll_rna

功能：遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。

函数原型：long long int __float2ll_rna(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的64位有符号整数。特殊值：±0→0；nan→0；inf→9223372036854775807（INT64_MAX）；-inf→-9223372036854775808（INT64_MIN）；ASCRT_MAX_NORMAL_F→9223372036854775807（INT64_MAX）。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [类型转换函数](type_conversion_functions.md)（`related`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__bfloat162ll_rna](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162ll_rna.md)（`same_topic`）：__bfloat162ll_rna：这些卡保持到long long的转换目标或RNA语义，只切换源类型、有符号性及RD/RN/RU/RZ舍入，可直接核对bfloat16边界值输出。 目标卡《__float2ll_rna》补充：遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。
- [__float2ll_rd](_float2ll_rd.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_rd》说明遵循CAST_FLOOR模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2ll_rn](_float2ll_rn.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_rn》说明遵循CAST_RINT模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2ll_ru](_float2ll_ru.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_ru》说明遵循CAST_CEIL模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__float2ll_rz](_float2ll_rz.md)（`same_topic`）：《__float2ll_rna》说明遵循CAST_ROUND模式，将浮点数转换为64位有符号整数，返回转换后的值。；《__float2ll_rz》说明遵循CAST_TRUNC模式，将浮点数转换为64位有符号整数，返回转换后的值。。二者在float到int64转换的rn/rna/rd/ru/rz差异完全由舍入合同决定，类型转换总览给出选择上下文上存在可执行的直接衔接。
- [__half2ll_rn](../../half_type/half_precision_conversion_functions/_half2ll_rn.md)（`same_topic`）：__half2ll_rn 与《__float2ll_rna》的实质衔接是：这些转换保持 half→long long 并切换舍入模式，或保持 RINT 改变源/目标有无符号；可直接核对 rn 的边界与溢出行为。
<!-- cannbot:related:end -->
