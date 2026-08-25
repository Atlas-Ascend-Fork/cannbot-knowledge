---
type: API
title: 数据类型转换概述
description: 类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。
tags: [task.lookup, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/data_type_conversion/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据类型转换概述

功能：类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。CAST_RINT：四舍六入五成双取整：srctype2dsttype_rn；CAST_FLOOR：向下取整：srctype2dsttype_rd；CAST_CEIL：向上取整：srctype2dsttype_ru；CAST_ROUND：四舍五入取整：srctype2dsttype_rna；CAST_TRUNC：向零取整：srctype2dsttype_rz。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../../simd_api/basic_api/memory_vector_compute/type_conversion/cast.md)（`related`）：SIMT 转换概述明确隐式/显式转换、舍入和饱和模式对结果的影响，可帮助把矢量 Cast 的 mode 选择映射到逐线程标量实现。
- [__float2uint_rd](type_conversion_functions/_float2uint_rd.md)（`related`）：《__float2uint_rd》说明遵循CAST_FLOOR模式，将浮点数转换为无符号整数，返回转换后的值。；《数据类型转换概述》说明类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。。二者在float到uint的rd/rn/rna/ru/rz决定边界整数结果，signed和half/bfloat16对应接口用于核对目标类型差异上存在可执行的直接衔接。
- [__float2uint_ru](type_conversion_functions/_float2uint_ru.md)（`related`）：《__float2uint_ru》说明遵循CAST_CEIL模式，将浮点数转换为无符号整数，返回转换后的值。；《数据类型转换概述》说明类型转换包括隐式转换和显式转换。隐式转换在类型不匹配时由系统自动执行。显式转换则通过调用类型转换API来主动完成，API会将输入数据从源类型转换为目标类型，并返回转换结果。整个转换过程遵循规定的处理规则。类型转换的结果受舍入模式和饱和模式的影响。关于浮点数的表示方式和舍入规则，请参见类型转换的相关说明。。二者在float到uint转换的rd/rn/rna/ru/rz仅舍入合同不同，类型转换总览提供这些模式的统一选择边界上存在可执行的直接衔接。
- [数据类型转换](data_type_conversion.md)（`same_topic`）：overview 解释隐式/显式转换、舍入和饱和如何决定结果，是本索引卡简述的完整语义契约。
<!-- cannbot:related:end -->
