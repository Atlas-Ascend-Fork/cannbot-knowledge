---
type: API
title: __float2uint_rd
description: 遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/type_conversion_functions/__float2uint_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __float2uint_rd

功能：遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。

函数原型：unsigned int __float2uint_rd(const float x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的无符号整数。特殊值：±0→0；nan→0；inf→4294967295；-inf→0。

约束：无。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__float2int_rd](_float2int_rd.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2int_rd》说明遵循CAST_FLOOR模式，将浮点数转换为有符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__half2uint_rd](../../half_type/half_precision_conversion_functions/_half2uint_rd.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__half2uint_rd》说明遵循CAST_FLOOR模式，将half类型数据转换为unsigned int类型数据，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [数据类型转换概述](../overview.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《数据类型转换概述》说明类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [类型转换函数](type_conversion_functions.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《类型转换函数》说明提供浮点数与整数（int、uint、ll、ull）之间遵循不同舍入模式的类型转换，以及位级重新解释函数列表。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__bfloat162uint_rd](../../bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162uint_rd.md)（`same_topic`）：__bfloat162uint_rd 与 __float2uint_rd 都按 CAST_FLOOR 转为 uint32；两者只在浮点源精度上不同，可用同一边界样例核对 floor 和饱和结果。
- [__float2uint_rn](_float2uint_rn.md)（`same_topic`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_rn》说明遵循CAST_RINT模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_rna](_float2uint_rna.md)（`same_topic`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_rna》说明遵循CAST_ROUND模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_ru](_float2uint_ru.md)（`same_topic`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_ru》说明遵循CAST_CEIL模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_rz](_float2uint_rz.md)（`same_topic`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《__float2uint_rz》说明遵循CAST_TRUNC模式，将浮点数转换为无符号整数，返回转换后的值。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
<!-- cannbot:related:end -->
